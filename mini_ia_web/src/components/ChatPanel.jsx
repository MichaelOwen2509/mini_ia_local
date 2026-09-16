import { useEffect, useRef, useState } from "react";
import { enviarPergunta } from "../api.js";

export default function ChatPanel({ notebookId, temDocumentos }) {
  const [mensagens, setMensagens] = useState([]);
  const [pergunta, setPergunta] = useState("");
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState("");
  const fimRef = useRef(null);

  useEffect(() => {
    fimRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [mensagens, carregando]);

  async function enviar(e) {
    e?.preventDefault();
    const texto = pergunta.trim();

    if (!texto || !notebookId || carregando) return;

    setPergunta("");
    setErro("");
    setMensagens((prev) => [...prev, { papel: "usuario", texto }]);
    setCarregando(true);

    try {
      const historico = mensagens.map((m) => ({
        papel: m.papel,
        texto: m.texto,
      }));

      const resposta = await enviarPergunta(notebookId, texto, historico);

      setMensagens((prev) => [
        ...prev,
        {
          papel: "ia",
          texto: resposta.resposta ?? resposta.answer ?? resposta.mensagem ?? "Não encontrei uma resposta.",
          fontes: resposta.fontes ?? resposta.sources ?? [],
        },
      ]);
    } catch (e) {
      setErro(e.message || "Não foi possível obter uma resposta.");
    } finally {
      setCarregando(false);
    }
  }

  const vazio = mensagens.length === 0;

  return (
    <main className="painel-chat">
      <header className="chat-cabecalho">
        <div>
          <span className="chat-status-dot" />
          <span>Mini IA</span>
        </div>
        <span className="chat-cabecalho-hint">
          {temDocumentos ? "Fontes carregadas" : "Adicione uma fonte para começar"}
        </span>
      </header>

      <div className="chat-mensagens">
        {vazio ? (
          <div className="chat-vazio">
            <div className="chat-vazio-icone">✦</div>
            <h2>O que você quer descobrir?</h2>
            <p>
              Adicione uma planilha na lateral e faça perguntas sobre os dados.
              A conversa fica ligada ao caderno selecionado.
            </p>

            {temDocumentos && (
              <div className="sugestoes">
                <button onClick={() => setPergunta("Qual o preço do produto?")}>
                  Qual o preço do produto?
                </button>
                <button onClick={() => setPergunta("Qual a categoria do produto?")}>
                  Qual a categoria do produto?
                </button>
                <button onClick={() => setPergunta("Quantas unidades temos?")}>
                  Quantas unidades temos?
                </button>
              </div>
            )}
          </div>
        ) : (
          mensagens.map((msg, i) => (
            <div
              key={i}
              className={`mensagem ${
                msg.papel === "usuario" ? "mensagem-usuario" : ""
              }`}
            >
              <div className="mensagem-avatar">
                {msg.papel === "usuario" ? "Você" : "IA"}
              </div>
              <div className="mensagem-coluna">
                <div className="mensagem-corpo">
                  <p>{msg.texto}</p>
                </div>

                {msg.fontes?.length > 0 && (
                  <div className="mensagem-fontes">
                    {msg.fontes.map((fonte, j) => (
                      <span className="fonte-chip" key={j}>
                        {typeof fonte === "string"
                          ? fonte
                          : fonte.nome ?? fonte.name ?? `Fonte ${j + 1}`}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {carregando && (
          <div className="mensagem">
            <div className="mensagem-avatar">IA</div>
            <div className="mensagem-coluna">
              <div className="mensagem-corpo">
                <div className="digitando">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={fimRef} />
      </div>

      <div className="chat-input-wrapper">
        {erro && <div className="chat-erro">{erro}</div>}

        <form className="chat-input-area" onSubmit={enviar}>
          <input
            value={pergunta}
            onChange={(e) => setPergunta(e.target.value)}
            placeholder={
              notebookId
                ? "Pergunte sobre suas planilhas..."
                : "Crie um caderno primeiro..."
            }
            disabled={!notebookId || carregando}
          />
          <button
            type="submit"
            disabled={!pergunta.trim() || !notebookId || carregando}
            title="Enviar pergunta"
          >
            ↑
          </button>
        </form>
        <p className="chat-disclaimer">
          A Mini IA responde com base nas fontes adicionadas ao caderno.
        </p>
      </div>
    </main>
  );
}
