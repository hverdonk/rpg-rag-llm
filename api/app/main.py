from fastapi import FastAPI
from app.models import AskRequest, AskResponse, Source
from app.ingest import scan_once
from app.retrieval import hybrid_search, maybe_rerank, assemble_context
from app.config import settings

app = FastAPI(title="Weaviate RPG RAG API")

@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ingest/scan")
def ingest_scan():
    stats = scan_once()
    return {"status": "ok", **stats}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest):
    filters = None
    if req.from_session or req.to_session:
        f = {"path": ["sessionNo"], "operator": "GreaterThan", "valueInt": 0}
        if req.from_session and req.to_session:
            filters = {"operator": "And", "operands": [
                {"path": ["sessionNo"], "operator": "GreaterThanEqual", "valueInt": req.from_session},
                {"path": ["sessionNo"], "operator": "LessThanEqual", "valueInt": req.to_session},
            ]}
        elif req.from_session:
            filters = {"path": ["sessionNo"], "operator": "GreaterThanEqual", "valueInt": req.from_session}
        elif req.to_session:
            filters = {"path": ["sessionNo"], "operator": "LessThanEqual", "valueInt": req.to_session}

    candidates = hybrid_search(req.query, k=req.k, filters=filters)
    top_items = maybe_rerank(req.query, candidates, settings.max_context_chunks)
    context = assemble_context(top_items, settings.max_context_chunks)

    # Here you would call your generator (LLM). For now we just return the context and stub an answer.
    # Replace the below with a call to your local/hosted LLM.
    answer_lines = [
        "Here is what I found:",
    ]
    for c in context:
        sec = c["heading"] or "(no heading)"
        ses = f"Session {c['sessionNo']}" if c.get("sessionNo") else ""
        answer_lines.append(f"- {ses} {c['doc_title']} § {sec}: …")

    sources = [
        Source(
            doc_title=c["doc_title"],
            session_no=c.get("sessionNo"),
            heading=c.get("heading"),
            path=c.get("path"),
            chunk_id=c.get("chunk_id"),
        ) for c in context
    ]

    return AskResponse(
        answer="\n".join(answer_lines),
        sources=sources,
        context=context,
    )