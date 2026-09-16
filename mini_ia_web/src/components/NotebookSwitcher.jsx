import { useState } from "react";

export default function NotebookSwitcher({
  notebooks,
  ativoId,
  onSelecionar,
  onCriar,
  onExcluir,
}) {
  const [criando, setCriando] = useState(false);
  const [nome, setNome] = useState("");

  async function criar(e) {
    e.preventDefault();
    const valor = nome.trim();
    if (!valor) return;
    await onCriar(valor);
    setNome("");
    setCriando(false);
  }

  async function excluir(id, nomeNotebook) {
    if (window.confirm(`Excluir o caderno "${nomeNotebook}"?`)) {
      await onExcluir(id);
    }
  }

  return (
    <section className="notebook-switcher">
      <div className="notebook-switcher-topo">
        <h2>Cadernos</h2>
        <button
          className="botao-icone"
          title="Novo caderno"
          onClick={() => setCriando((v) => !v)}
        >
          +
        </button>
      </div>

      {criando && (
        <form className="form-novo-notebook" onSubmit={criar}>
          <input
            autoFocus
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            placeholder="Nome do caderno"
          />
          <button disabled={!nome.trim()}>Criar</button>
        </form>
      )}

      {notebooks.length === 0 ? (
        <p className="lista-vazia">Crie um caderno para começar.</p>
      ) : (
        <ul className="lista-notebooks">
          {notebooks.map((notebook) => (
            <li
              key={notebook.id}
              className={notebook.id === ativoId ? "notebook-ativo" : ""}
            >
              <button
                className="notebook-nome-botao"
                onClick={() => onSelecionar(notebook.id)}
              >
                <span className="mini-icone">▱</span>
                {notebook.nome}
              </button>
              <button
                className="botao-excluir"
                title="Excluir caderno"
                onClick={() => excluir(notebook.id, notebook.nome)}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
