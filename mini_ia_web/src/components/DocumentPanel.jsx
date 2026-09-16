import { useRef, useState } from "react";
import { enviarArquivo, excluirDocumento } from "../api.js";

export default function DocumentPanel({
  notebookId,
  documentos,
  carregando,
  onNovoDocumento,
  onExcluirDocumento,
}) {
  const inputRef = useRef(null);
  const [arrastando, setArrastando] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState("");

  async function processarArquivo(arquivo) {
    if (!notebookId || !arquivo) return;

    const permitido = /\.(xlsx|xls|csv)$/i.test(arquivo.name);
    if (!permitido) {
      setErro("Envie um arquivo Excel (.xlsx/.xls) ou CSV.");
      return;
    }

    setErro("");
    setEnviando(true);

    try {
      const doc = await enviarArquivo(notebookId, arquivo);
      onNovoDocumento(doc);
    } catch (e) {
      setErro(e.message || "Não foi possível enviar o arquivo.");
    } finally {
      setEnviando(false);
    }
  }

  async function remover(doc) {
    if (!window.confirm(`Remover "${doc.nome}"?`)) return;

    try {
      await excluirDocumento(notebookId, doc.id);
      onExcluirDocumento(doc.id);
    } catch (e) {
      setErro(e.message || "Não foi possível remover o arquivo.");
    }
  }

  return (
    <section className="documentos-painel">
      <div className="documentos-titulo">
        <h2>Fontes</h2>
        {documentos.length > 0 && (
          <span className="contador">{documentos.length}</span>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".xlsx,.xls,.csv"
        hidden
        onChange={(e) => {
          processarArquivo(e.target.files?.[0]);
          e.target.value = "";
        }}
      />

      <button
        className={`zona-upload ${!notebookId ? "desabilitada" : ""} ${
          arrastando ? "arrastando" : ""
        }`}
        disabled={!notebookId || enviando}
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setArrastando(true);
        }}
        onDragLeave={() => setArrastando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastando(false);
          processarArquivo(e.dataTransfer.files?.[0]);
        }}
      >
        <span className="zona-upload-icone">↑</span>
        <p>{enviando ? "Processando arquivo..." : "Adicionar uma fonte"}</p>
        <span className="zona-upload-formatos">
          Arraste aqui ou clique para escolher
          <br />
          Excel ou CSV
        </span>
      </button>

      {erro && <p className="status-erro">{erro}</p>}

      <div className="lista-documentos">
        <h2>Arquivos adicionados</h2>

        {carregando ? (
          <p className="lista-vazia">Carregando...</p>
        ) : documentos.length === 0 ? (
          <p className="lista-vazia">
            Nenhum arquivo ainda. Adicione uma planilha para começar.
          </p>
        ) : (
          <ul>
            {documentos.map((doc) => (
              <li key={doc.id}>
                <span className="doc-icone">▤</span>
                <span className="doc-nome" title={doc.nome}>
                  {doc.nome}
                </span>
                <button
                  className="doc-remover"
                  title="Remover arquivo"
                  onClick={() => remover(doc)}
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
