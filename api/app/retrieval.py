from typing import List, Dict, Any
from app.weaviate_client import get_client
from app.embeddings import embed_texts, get_reranker
from app.config import settings
from weaviate.classes.query import Filter


def hybrid_search(query: str, k: int = 30, filters: Filter | None = None) -> List[Dict[str, Any]]:
    client = get_client()
    chunks = client.collections.get("Chunk")
    
    response = chunks.query.hybrid(
        query=query,
        limit=k,
        alpha=0.5,
        return_metadata=["score", "distance"],
        return_references=["ofDoc", "characters", "locations", "organizations"],
        where=filters
    )
    
    results = []
    for obj in response.objects:
        # Safe reference handling
        doc_ref = obj.references.get("ofDoc") if obj.references else None
        
        result = {
            "text": obj.properties["text"],
            "heading": obj.properties["heading"],
            "sessionNo": obj.properties["sessionNo"],
            "sessionDate": obj.properties["sessionDate"],
            "doc_title": doc_ref.properties["title"] if doc_ref else None,
            "path": doc_ref.properties["path"] if doc_ref else None,
            "chunk_id": str(obj.uuid),
            "score": obj.metadata.score if obj.metadata else None,
            "distance": obj.metadata.distance if obj.metadata else None,
            "characters": [{
                "name": char.properties["name"],
                "path": char.properties["path"]
            } for char in (obj.references.get("characters", []) if obj.references else [])],
            "locations": [{
                "name": loc.properties["name"],
                "path": loc.properties["path"]
            } for loc in (obj.references.get("locations", []) if obj.references else [])],
            "organizations": [{
                "name": org.properties["name"],
                "path": org.properties["path"]
            } for org in (obj.references.get("organizations", []) if obj.references else [])]
        }
        results.append(result)
    
    return results


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
    for item in items:
        key = (item["doc_title"], item["heading"])
        if key in seen:
            continue
        seen.add(key)
        out.append({
            "text": item["text"],
            "heading": item["heading"],
            "doc_title": item["doc_title"],
            "path": item["path"],
            "sessionNo": item["sessionNo"],
            "sessionDate": item["sessionDate"],
            "chunk_id": item["chunk_id"],
        })
        if len(out) >= max_chunks:
            break
    return out