import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from brain import RedeNeural
from database import (
    adicionar_excel_arquivo,
    buscar_produto,
    criar_tabela,
    listar_nomes_produtos,
)
from text import normalizar, tokenizar

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
MODELO = BASE_DIR / "modelo_rede.npz"

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "estoque")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "admin")

app = FastAPI(title="Mini IA — API local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NotebookRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=200)


class Mensagem(BaseModel):
    role: str
    content: str


class PerguntaRequest(BaseModel):
    pergunta: str
    historico: list[Mensagem] = Field(default_factory=list)


def conectar():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def criar_tabelas_web():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mini_ia_cadernos (
            id UUID PRIMARY KEY,
            nome TEXT NOT NULL,
            criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mini_ia_documentos (
            id UUID PRIMARY KEY,
            caderno_id UUID NOT NULL REFERENCES mini_ia_cadernos(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            extensao TEXT NOT NULL,
            adicionado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            produtos_adicionados INTEGER NOT NULL DEFAULT 0
        );
    """)
    conn.commit()
    cur.close()
    conn.close()


def rede_carregada():
    if not MODELO.exists():
        raise HTTPException(
            400,
            "A rede neural ainda não foi treinada. Use POST /treinar primeiro."
        )
    try:
        return RedeNeural.carregar(str(MODELO))
    except Exception as e:
        raise HTTPException(500, f"Não foi possível carregar a rede neural: {e}") from e


def extrair_produto(pergunta):
    palavras_pergunta = set(tokenizar(pergunta))
    palavras_ignoradas = {
        "o", "a", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
        "quanto", "quantos", "quantas", "qual", "quais", "onde", "fica", "esta",
        "tem", "temos", "tenho", "vc", "voce", "e", "em", "é", "foi", "quando",
        "me", "diga", "fala", "falame", "quero", "saber", "para", "pelo", "produto",
    }
    palavras_pergunta -= palavras_ignoradas

    produtos = listar_nomes_produtos()
    melhor_produto = None
    melhor_pontuacao = 0

    for produto in produtos:
        palavras_produto = set(tokenizar(produto))
        palavras_produto -= palavras_ignoradas
        coincidencias = palavras_produto & palavras_pergunta
        pontuacao = len(coincidencias)
        if pontuacao > melhor_pontuacao:
            melhor_pontuacao = pontuacao
            melhor_produto = produto

    return melhor_produto


def responder(rede, intencao, pergunta):
    if intencao == "desconhecido":
        return "Não sei responder esse tipo de pergunta."

    produto = extrair_produto(pergunta)
    if produto is None:
        return "Não encontrei esse produto."

    dados = buscar_produto(produto)
    if dados is None:
        return "Não encontrei esse produto no banco."

    nome = dados[0]
    respostas = {
        "preco": f"O {nome} custa R$ {dados[3]:.2f}.",
        "quantidade": f"Temos {dados[2]} unidades de {nome}.",
        "localizacao": f"O {nome} está em {dados[5]}.",
        "fornecedor": f"O fornecedor do {nome} é {dados[4]}.",
        "ultima_compra": (
            f"A última compra do {nome} foi em "
            f"{dados[6].strftime('%d/%m/%Y')}."
        ),
        "categoria": f"O {nome} pertence à categoria {dados[1]}.",
    }
    return respostas[intencao]


def listar_cadernos():
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, c.nome, c.criado_em, COUNT(d.id)
        FROM mini_ia_cadernos c
        LEFT JOIN mini_ia_documentos d ON d.caderno_id = c.id
        GROUP BY c.id
        ORDER BY c.criado_em DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {"id": str(r[0]), "nome": r[1], "criado_em": r[2].isoformat(), "total_documentos": r[3]}
        for r in rows
    ]


def caderno_existe(caderno_id):
    conn = conectar()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM mini_ia_cadernos WHERE id = %s", (str(caderno_id),))
    ok = cur.fetchone() is not None
    cur.close()
    conn.close()
    return ok


@app.on_event("startup")
def startup():
    criar_tabela()
    criar_tabelas_web()


@app.get("/")
def raiz():
    return {"status": "ok", "servico": "Mini IA local", "ia_externa": False}


@app.get("/status")
def status():
    return {
        "banco": "PostgreSQL local",
        "rede_neural": MODELO.exists(),
        "modelo": str(MODELO.name),
        "ia_externa": False,
    }


@app.post("/treinar")
def treinar():
    try:
        rede = RedeNeural()
        rede.treinar()
        rede.salvar(str(MODELO))
        return {"ok": True, "mensagem": "Rede neural treinada e salva.", "modelo": MODELO.name}
    except Exception as e:
        raise HTTPException(500, f"Erro ao treinar a rede neural: {e}") from e


@app.get("/notebooks")
def get_notebooks():
    return listar_cadernos()


@app.post("/notebooks")
def post_notebook(req: NotebookRequest):
    nome = req.nome.strip()
    if not nome:
        raise HTTPException(400, "Nome do caderno não pode ser vazio")
    notebook_id = uuid4()
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO mini_ia_cadernos (id, nome) VALUES (%s, %s)",
        (str(notebook_id), nome),
    )
    conn.commit()
    cur.close()
    conn.close()
    return {"id": str(notebook_id), "nome": nome, "total_documentos": 0}


@app.delete("/notebooks/{notebook_id}")
def delete_notebook(notebook_id: UUID):
    if not caderno_existe(notebook_id):
        raise HTTPException(404, "Caderno não encontrado")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("DELETE FROM mini_ia_cadernos WHERE id = %s", (str(notebook_id),))
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}


@app.get("/notebooks/{notebook_id}/documentos")
def get_documentos(notebook_id: UUID):
    if not caderno_existe(notebook_id):
        raise HTTPException(404, "Caderno não encontrado")
    conn = conectar()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, nome, extensao, adicionado_em, produtos_adicionados
        FROM mini_ia_documentos
        WHERE caderno_id = %s
        ORDER BY adicionado_em DESC;
    """, (str(notebook_id),))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": str(r[0]),
            "nome": r[1],
            "extensao": r[2],
            "adicionado_em": r[3].isoformat(),
            "produtos_adicionados": r[4],
        }
        for r in rows
    ]


@app.post("/notebooks/{notebook_id}/upload")
async def upload_excel(notebook_id: UUID, file: UploadFile = File(...)):
    if not caderno_existe(notebook_id):
        raise HTTPException(404, "Caderno não encontrado")

    nome = file.filename or "arquivo"
    extensao = Path(nome).suffix.lower()
    if extensao not in {".xlsx", ".xls", ".csv"}:
        raise HTTPException(400, "Envie .xlsx, .xls ou .csv")

    fd, caminho = tempfile.mkstemp(suffix=extensao)
    os.close(fd)
    try:
        with open(caminho, "wb") as destino:
            shutil.copyfileobj(file.file, destino)

        adicionados = adicionar_excel_arquivo(caminho)
        documento_id = uuid4()

        conn = conectar()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO mini_ia_documentos
                (id, caderno_id, nome, extensao, produtos_adicionados)
            VALUES (%s, %s, %s, %s, %s)
        """, (str(documento_id), str(notebook_id), nome, extensao, adicionados))
        conn.commit()
        cur.close()
        conn.close()

        return {
            "id": str(documento_id),
            "nome": nome,
            "extensao": extensao,
            "produtos_adicionados": adicionados,
            "mensagem": f"Arquivo processado. {adicionados} produto(s) novo(s) adicionado(s) ao banco.",
        }
    except Exception as e:
        raise HTTPException(500, f"Erro ao processar arquivo: {e}") from e
    finally:
        if os.path.exists(caminho):
            os.remove(caminho)


@app.delete("/notebooks/{notebook_id}/documentos/{documento_id}")
def delete_documento(notebook_id: UUID, documento_id: UUID):
    if not caderno_existe(notebook_id):
        raise HTTPException(404, "Caderno não encontrado")
    conn = conectar()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM mini_ia_documentos WHERE id = %s AND caderno_id = %s",
        (str(documento_id), str(notebook_id)),
    )
    if cur.rowcount == 0:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(404, "Documento não encontrado")
    conn.commit()
    cur.close()
    conn.close()
    return {"ok": True}


@app.post("/notebooks/{notebook_id}/chat")
def chat(notebook_id: UUID, req: PerguntaRequest):
    if not caderno_existe(notebook_id):
        raise HTTPException(404, "Caderno não encontrado")

    pergunta = req.pergunta.strip()
    if not pergunta:
        raise HTTPException(400, "Pergunta vazia")

    rede = rede_carregada()
    intencao, confianca = rede.prever(pergunta)

    if intencao is None:
        return {
            "resposta": "Ainda não sei responder esse tipo de pergunta.",
            "intencao": None,
            "confianca": confianca,
            "fontes": [],
        }

    resposta = responder(rede, intencao, pergunta)
    produto = extrair_produto(pergunta)
    return {
        "resposta": resposta,
        "intencao": intencao,
        "confianca": confianca,
        "produto": produto,
        "fontes": [produto] if produto else [],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
