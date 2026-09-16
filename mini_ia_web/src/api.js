const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function tratarResposta(res) {
  if (!res.ok) {
    const dados = await res.json().catch(() => ({}));
    throw new Error(dados.detail || `Erro ${res.status}`);
  }
  return res.json();
}

export async function listarNotebooks() {
  const res = await fetch(`${API_URL}/notebooks`);
  return tratarResposta(res);
}

export async function criarNotebook(nome) {
  const res = await fetch(`${API_URL}/notebooks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome }),
  });
  return tratarResposta(res);
}

export async function excluirNotebook(notebookId) {
  const res = await fetch(`${API_URL}/notebooks/${notebookId}`, { method: "DELETE" });
  return tratarResposta(res);
}

export async function listarDocumentos(notebookId) {
  const res = await fetch(`${API_URL}/notebooks/${notebookId}/documentos`);
  return tratarResposta(res);
}

export async function enviarArquivo(notebookId, arquivo) {
  const formData = new FormData();
  formData.append("file", arquivo);
  const res = await fetch(`${API_URL}/notebooks/${notebookId}/upload`, {
    method: "POST",
    body: formData,
  });
  return tratarResposta(res);
}

export async function excluirDocumento(notebookId, documentoId) {
  const res = await fetch(`${API_URL}/notebooks/${notebookId}/documentos/${documentoId}`, {
    method: "DELETE",
  });
  return tratarResposta(res);
}

export async function enviarPergunta(notebookId, pergunta, historico) {
  const historicoApi = historico.map((item) => ({
    role: item.papel,
    content: item.texto,
  }));

  const dados = {
    pergunta,
    historico: historicoApi,
  };

  console.log("ENVIANDO PARA API:", dados);

  const res = await fetch(
    `${API_URL}/notebooks/${notebookId}/chat`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(dados),
    }
  );

  const resposta = await res.json();

  console.log("RESPOSTA DA API:", resposta);

  if (!res.ok) {
    throw new Error(
      typeof resposta.detail === "string"
        ? resposta.detail
        : JSON.stringify(resposta.detail)
    );
  }

  return resposta;
}