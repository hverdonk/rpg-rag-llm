# RPG RAG LLM Starter Repo

A minimal FastAPI + Weaviate project to index Markdown-format RPG session/character notes with [[WikiLinks]], run hybrid retrieval (BM25 + vector), 
optionally rerank on CPU, and answer questions (Discord‑ready).

## File tree
```
rpg-rag-llm/
├─ compose.yml
├─ .env.example
├─ README.md
├─ api/
│ ├─ Dockerfile
│ ├─ requirements.txt
│ └─ app/
│ ├─ main.py
│ ├─ config.py
│ ├─ models.py
│ ├─ weaviate_client.py
│ ├─ embeddings.py
│ ├─ ingest.py
│ ├─ retrieval.py
│ └─ utils.py
```
