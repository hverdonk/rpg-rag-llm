from fastapi import FastAPI
from app.models import AskRequest, AskResponse, Source
from app.ingest import scan_once
from app.retrieval import hybrid_search, maybe_rerank, assemble_context
from app.config import settings
from app.generator import generate_answer
from weaviate.classes.query import Filter

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
        if req.from_session and req.to_session:
            filters = Filter.all_of([
                Filter.by_property("sessionNo").greater_or_equal(req.from_session),
                Filter.by_property("sessionNo").less_or_equal(req.to_session)
            ])
        elif req.from_session:
            filters = Filter.by_property("sessionNo").greater_or_equal(req.from_session)
        elif req.to_session:
            filters = Filter.by_property("sessionNo").less_or_equal(req.to_session)

    candidates = hybrid_search(req.query, k=req.k, filters=filters)
    top_items = maybe_rerank(req.query, candidates, settings.max_context_chunks)
    context = assemble_context(top_items, settings.max_context_chunks)

    answer = generate_answer(req.query, context, max_tokens=400)

    sources = [Source(
        doc_title=c.get("doc_title") or "Unknown Document", 
        session_no=c.get("sessionNo"),
        heading=c.get("heading"), 
        path=c.get("path"), 
        chunk_id=c.get("chunk_id") or ""
    ) for c in context]

    return AskResponse(answer=answer, sources=sources, context=context)
