import { useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel.jsx";
import DocumentPanel from "./components/DocumentPanel.jsx";
import NotebookSwitcher from "./components/NotebookSwitcher.jsx";
import {
  criarNotebook,
  excluirNotebook,
  listarDocumentos,
  listarNotebooks,
} from "./api.js";

export default function App() {
  const [notebooks, setNotebooks] = useState([]);
  const [notebookAtivoId, setNotebookAtivoId] = useState(null);
  const [documentos, setDocumentos] = useState([]);
  const [carregandoDocs, setCarregandoDocs] = useState(false);

  useEffect(() => {
    listarNotebooks()
      .then((lista) => {
        setNotebooks(lista);
        if (lista.length > 0) setNotebookAtivoId(lista[0].id);
      })
      .catch(console.error);
  }, []);

  useEffect(() => {
    if (!notebookAtivoId) {
      setDocumentos([]);
      return;
    }

    setCarregandoDocs(true);
    listarDocumentos(notebookAtivoId)
      .then(setDocumentos)
      .catch(() => setDocumentos([]))
      .finally(() => setCarregandoDocs(false));
  }, [notebookAtivoId]);

  async function handleCriarNotebook(nome) {
    const novo = await criarNotebook(nome);
    setNotebooks((prev) => [novo, ...prev]);
    setNotebookAtivoId(novo.id);
  }

  async function handleExcluirNotebook(id) {
    await excluirNotebook(id);
    setNotebooks((prev) => {
      const restantes = prev.filter((n) => n.id !== id);
      if (notebookAtivoId === id) {
        setNotebookAtivoId(restantes[0]?.id ?? null);
      }
      return restantes;
    });
  }

  function handleNovoDocumento(doc) {
    setDocumentos((prev) => [...prev, doc]);
  }

  function handleExcluirDocumento(docId) {
    setDocumentos((prev) => prev.filter((d) => d.id !== docId));
  }

  return (
    <div className="app-layout">
      <aside className="coluna-lateral">
        <div className="marca">
          <span className="marca-simbolo">✦</span>
          <h1>Mini IA</h1>
        </div>
        <p className="marca-subtitulo">Seu caderno de dados com IA</p>

        <NotebookSwitcher
          notebooks={notebooks}
          ativoId={notebookAtivoId}
          onSelecionar={setNotebookAtivoId}
          onCriar={handleCriarNotebook}
          onExcluir={handleExcluirNotebook}
        />

        <DocumentPanel
          notebookId={notebookAtivoId}
          documentos={documentos}
          carregando={carregandoDocs}
          onNovoDocumento={handleNovoDocumento}
          onExcluirDocumento={handleExcluirDocumento}
        />
      </aside>

      <ChatPanel
        key={notebookAtivoId || "sem-caderno"}
        notebookId={notebookAtivoId}
        temDocumentos={documentos.length > 0}
      />
    </div>
  );
}
