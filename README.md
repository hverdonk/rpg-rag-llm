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
1) Copy .env.example to .env and set the paths to your notes and any other environment variables.

2) Start services:
`docker compose up -d --build`

3) Seed index (one‑off scan):
`curl -X POST http://localhost:8000/ingest/scan`

4) Ask a question:
    ```
    curl -s -X POST http://localhost:8000/ask \
    -H 'Content-Type: application/json' \
    -d '{"query":"What did Varin do in the Ice Village?","k":30}' | jq
    ```

5) (Optional) Open Weaviate GraphQL console: http://localhost:8080/v1/graphql


## Notes format
- Session notes and character notes are Markdown.
- `[[Varin]]` in text links to `characters/Varin.md`.
- `[[Ice Village]]` in text links to `locations/Ice Village.md`.
- `[[Army of the West]]` in text links to `organizations/Army of the West.md`.
- Supports pipe syntax: `[[filename|display name]]` and paths: `[[path/to/file|display]]`.
- The ingester extracts headings, chunks by section, embeds on CPU, upserts to Weaviate.


## Models (local CPU by default)
- Embeddings: `BAAI/bge-small-en-v1.5` (384‑d). Change via `EMBED_MODEL_NAME`.
- Reranker (optional): `BAAI/bge-reranker-base`. Enable with `ENABLE_RERANKER=true`.
- Generator: Choose between local Ollama or Google Gemini via `GENERATOR_PROVIDER`.


## Environment
Set envs in `compose.yml` or `.env`. For large repos, use SSD for Weaviate volume.
```
WEAVIATE_URL=http://weaviate:8080 
NOTES_SESSIONS_DIR=/notes/sessions 
NOTES_CHARACTERS_DIR=/notes/characters
NOTES_LOCATIONS_DIR=/notes/locations
NOTES_ORGANIZATIONS_DIR=/notes/organizations

# Generator Configuration
GENERATOR_PROVIDER=ollama  # or "gemini"

# Ollama settings (when using ollama)
OLLAMA_BASE_URL=http://ollama:11434
OLLAMA_MODEL_NAME=llama3.1:8b-instruct-q4_K_M

# Gemini settings (when using gemini)
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
```

## Generator Providers

### Using Ollama (Default)
The system uses Ollama by default for local LLM generation. Ensure the Ollama service is running and the specified model is available.

### Using Google Gemini
To use Google Gemini instead of Ollama:
1. Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set `GENERATOR_PROVIDER=gemini` in your environment
3. Set `GEMINI_API_KEY=your_actual_api_key`
4. Optionally configure `GEMINI_MODEL_NAME` (defaults to `gemini-1.5-flash`)

When using Gemini, the Ollama service is not required and can be removed from the docker-compose.yml if desired.

## Roadmap
- File watcher (watchdog) container/sidecar
- Alias table from front‑matter
- Discord bot commands