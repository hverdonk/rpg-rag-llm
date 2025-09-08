from typing import List, Dict, Any
from app.weaviate_client import get_client
from app.embeddings import embed_texts, get_reranker
from app.config import settings
from weaviate.classes.query import Filter, QueryReference


def hybrid_search(query: str, k: int = 30, filters: Filter | None = None) -> List[Dict[str, Any]]:
    client = get_client()
    chunks = client.collections.get("Chunk")
    query_vector = embed_texts([query])[0]
    
    if filters:
        response = chunks.query.hybrid(
            query=query,
            vector=query_vector,
            limit=k,
            alpha=0.5,
            return_metadata=["score", "distance"],
            return_references=[
                QueryReference(link_on="ofDoc"),
                QueryReference(link_on="characters"),
                QueryReference(link_on="locations"),
                QueryReference(link_on="organizations")
            ]
        ).where(filters)
    else:
        response = chunks.query.hybrid(
            query=query,
            vector=query_vector,
            limit=k,
            alpha=0.5,
            return_metadata=["score", "distance"],
            return_references=[
                QueryReference(link_on="ofDoc"),
                QueryReference(link_on="characters"),
                QueryReference(link_on="locations"),
                QueryReference(link_on="organizations")
            ]
        )
    
    results = []
    for obj in response.objects:
        result = {
            "text": obj.properties["text"],
            "heading": obj.properties["heading"],
            "sessionNo": obj.properties["sessionNo"],
            "sessionDate": obj.properties["sessionDate"],
            "doc_title": None,
            "path": None,
            "chunk_id": str(obj.uuid),
            "score": obj.metadata.score if obj.metadata else None,
            "distance": obj.metadata.distance if obj.metadata else None,
            "characters": [],
            "locations": [],
            "organizations": []
        }
        
        # Handle references - they are returned as objects with properties
        if hasattr(obj, 'references') and obj.references:
            # Document reference
            if "ofDoc" in obj.references and obj.references["ofDoc"]:
                doc_obj = obj.references["ofDoc"]
                if hasattr(doc_obj, 'properties'):
                    result["doc_title"] = doc_obj.properties.get("title")
                    result["path"] = doc_obj.properties.get("path")
            
            # Character references
            if "characters" in obj.references:
                chars = obj.references["characters"]
                if chars:
                    # Handle both single objects and lists
                    char_list = chars if isinstance(chars, list) else [chars]
                    for char in char_list:
                        if hasattr(char, 'properties'):
                            result["characters"].append({
                                "name": char.properties.get("name"),
                                "path": char.properties.get("path")
                            })
            
            # Location references
            if "locations" in obj.references:
                locs = obj.references["locations"]
                if locs:
                    # Handle both single objects and lists
                    loc_list = locs if isinstance(locs, list) else [locs]
                    for loc in loc_list:
                        if hasattr(loc, 'properties'):
                            result["locations"].append({
                                "name": loc.properties.get("name"),
                                "path": loc.properties.get("path")
                            })
            
            # Organization references
            if "organizations" in obj.references:
                orgs = obj.references["organizations"]
                if orgs:
                    # Handle both single objects and lists
                    org_list = orgs if isinstance(orgs, list) else [orgs]
                    for org in org_list:
                        if hasattr(org, 'properties'):
                            result["organizations"].append({
                                "name": org.properties.get("name"),
                                "path": org.properties.get("path")
                            })
        
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