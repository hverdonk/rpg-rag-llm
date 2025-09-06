from typing import List, Dict, Any
from app.weaviate_client import get_client
from app.embeddings import embed_texts, get_reranker
from app.config import settings


def hybrid_search(query: str, k: int = 30, filters: dict | None = None) -> List[Dict[str, Any]]:
    client = get_client()
    # We use GraphQL via the Python client
    q = client.query.get("Chunk", [
        "text", "heading", "sessionNo", "sessionDate",
        "ofDoc { ... on Document { title path sessionNo sessionDate } }",
        "characters { ... on Character { name path } }",
        "_additional { id score distance }",
    ]).with_limit(k).with_hybrid(query=query, alpha=0.5)

    if filters:
        q = q.with_where(filters)

    res = q.do()
    items = res.get("data", {}).get("Get", {}).get("Chunk", [])
    return items


def maybe_rerank(query: str, items: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
    reranker = get_reranker()
    if not reranker or not items:
        return items[:top_n]
    pairs = [(query, it.get("text", "")) for it in items]
    scores = reranker.predict(pairs)
    ranked = sorted(zip(items, scores), key=lambda x: x[1], reverse=True)
    return [it for it, _ in ranked[:top_n]]


def assemble_context(items: List[Dict[str, Any]], max_chunks: int) -> List[Dict[str, Any]]:
    # Coalesce by document+heading to encourage diversity
    seen = set()
    out = []
    for it in items:
        doc = it.get("ofDoc", {})
        key = (doc.get("title"), it.get("heading"))
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "text": it.get("text"),
            "heading": it.get("heading"),
            "doc_title": doc.get("title"),
            "path": doc.get("path"),
            "sessionNo": doc.get("sessionNo"),
            "sessionDate": doc.get("sessionDate"),
            "chunk_id": it.get("_additional", {}).get("id"),
        })
        if len(out) >= max_chunks:
            break
    return out