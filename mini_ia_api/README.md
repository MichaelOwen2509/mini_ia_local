# Mini IA — API local

Esta versão usa somente o código local do projeto:

- `brain.py`: nossa rede neural de classificação de intenção.
- `database.py`: PostgreSQL com os produtos do Excel.
- `text.py`: normalização/tokenização.
- `main.py`: FastAPI, apenas fazendo a ligação entre frontend, rede e banco.

**Não usa Gemini, OpenAI, LangChain, RAG, embeddings ou qualquer API externa de IA.**

## 1. Instalar

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. PostgreSQL

A API usa o mesmo banco do projeto:

- banco: `estoque`
- usuário: `admin`
- senha: `admin`
- host: `localhost`
- porta: `5432`

## 3. Treinar a rede

Dentro desta pasta:

```bash
python -c "from brain import RedeNeural; r=RedeNeural(); r.treinar(); r.salvar('modelo_rede.npz')"
```

Isso cria `modelo_rede.npz`.

## 4. Iniciar API

```bash
uvicorn main:app --reload --port 8000
```

Abra `http://127.0.0.1:8000/docs` para testar.

## 5. Iniciar frontend

Na pasta do frontend:

```bash
npm install
npm run dev
```

A interface usa `http://127.0.0.1:8000` por padrão.
