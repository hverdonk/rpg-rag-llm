# RPG RAG LLM Starter Repo

This repo indexes Markdown notes for a long‑running RPG (sessions + characters with `[[WikiLinks]]`) into Weaviate and exposes a FastAPI endpoint for retrieval‑augmented answers.


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
│   ├─ main.py
│   ├─ config.py
│   ├─ models.py
│   ├─ weaviate_client.py
│   ├─ embeddings.py
│   ├─ ingest.py
│   ├─ retrieval.py
│   └─ utils.py
```


# Quick start
1) Put your notes under:
`./data/notes/sessions/.md ./data/notes/characters/.md`

2) Start services:
`docker compose up -d --build`

3) Seed index (one‑off scan):
`curl -X POST http://localhost:8000/ingest/scan`

4) Ask a question:
    ```
    curl -s -X POST http://localhost:8000/ask
    -H 'Content-Type: application/json'
    -d '{"query":"What did Varin do in the Ice Village?","k":30}' | jq
    ```

5) (Optional) Open Weaviate GraphQL console: http://localhost:8080/v1/graphql


## Notes format
- Session notes and character notes are Markdown.
- `[[Varin]]` in text links to `characters/Varin.md`.
- The ingester extracts headings, chunks by section, embeds on CPU, upserts to Weaviate.


## Models (local CPU by default)
- Embeddings: `BAAI/bge-small-en-v1.5` (384‑d). Change via `EMBED_MODEL_NAME`.
- Reranker (optional): `BAAI/bge-reranker-base`. Enable with `ENABLE_RERANKER=true`.
- Generator: out of scope here; wire your Discord bot to call `/ask` and then hit a local/hosted LLM with the returned `context`.


## Environment
Set envs in `docker-compose.yml` or `.env`. For large repos, use SSD for Weaviate volume.
```
WEAVIATE_URL=http://weaviate:8080 
NOTES_SESSIONS_DIR=/notes/sessions 
NOTES_CHARACTERS_DIR=/notes/characters
```

## Roadmap
- File watcher (watchdog) container/sidecar
- Alias table from front‑matter
- Discord bot commands