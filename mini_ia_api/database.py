import os
from pathlib import Path

import pandas as pd
import psycopg2

DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "estoque"
DB_USER = "admin"
DB_PASSWORD = "admin"
ARQUIVO_EXCEL = "Planilha1.xlsx"

COLUNAS = [
    "Nome_Item", "Categoria", "Quantidade", "Preco_Unitario",
    "Fornecedor", "Localizacao_Estoque", "Data_Ultima_Compra"
]


def conectar():
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASSWORD
    )


def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id SERIAL PRIMARY KEY,
            nome_item TEXT NOT NULL,
            categoria TEXT,
            quantidade INTEGER,
            preco_unitario NUMERIC(12, 2),
            fornecedor TEXT,
            localizacao_estoque TEXT,
            data_ultima_compra DATE
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()


def _ler_arquivo(caminho):
    ext = Path(caminho).suffix.lower()
    if ext == ".csv":
        df = pd.read_csv(caminho)
    else:
        df = pd.read_excel(caminho)

    for coluna in COLUNAS:
        if coluna not in df.columns:
            raise ValueError(f"Coluna '{coluna}' não encontrada no arquivo.")
    return df


def importar_excel():
    return importar_excel_arquivo(ARQUIVO_EXCEL)


def importar_excel_arquivo(caminho):
    df = _ler_arquivo(caminho)
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM produtos;")
    for _, linha in df.iterrows():
        _inserir(cursor, linha)
    conn.commit()
    cursor.close()
    conn.close()
    return len(df)


def adicionar_excel():
    return adicionar_excel_arquivo(ARQUIVO_EXCEL)


def adicionar_excel_arquivo(caminho):
    """Adiciona somente produtos que ainda não existem, sem apagar o banco."""
    df = _ler_arquivo(caminho)
    conn = conectar()
    cursor = conn.cursor()
    adicionados = 0
    try:
        for _, linha in df.iterrows():
            nome = str(linha["Nome_Item"]).strip()
            if not nome or nome.lower() == "nan":
                continue
            cursor.execute(
                "SELECT 1 FROM produtos WHERE LOWER(nome_item) = LOWER(%s) LIMIT 1",
                (nome,)
            )
            if cursor.fetchone() is not None:
                continue
            _inserir(cursor, linha, nome)
            adicionados += 1
        conn.commit()
    finally:
        cursor.close()
        conn.close()
    return adicionados


def _inserir(cursor, linha, nome=None):
    nome = nome or str(linha["Nome_Item"]).strip()
    data = linha["Data_Ultima_Compra"]
    if pd.isna(data):
        data = None
    cursor.execute("""
        INSERT INTO produtos (
            nome_item, categoria, quantidade, preco_unitario,
            fornecedor, localizacao_estoque, data_ultima_compra
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
    """, (
        nome, linha["Categoria"], int(linha["Quantidade"]),
        float(linha["Preco_Unitario"]), linha["Fornecedor"],
        linha["Localizacao_Estoque"], data
    ))


def buscar_produto(nome):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT nome_item, categoria, quantidade, preco_unitario,
               fornecedor, localizacao_estoque, data_ultima_compra
        FROM produtos
        WHERE LOWER(nome_item) LIKE LOWER(%s)
        LIMIT 1;
    """, (f"%{nome}%",))
    produto = cursor.fetchone()
    cursor.close()
    conn.close()
    return produto


def listar_nomes_produtos():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT nome_item FROM produtos ORDER BY LENGTH(nome_item) DESC;")
    produtos = [linha[0] for linha in cursor.fetchall()]
    cursor.close()
    conn.close()
    return produtos
