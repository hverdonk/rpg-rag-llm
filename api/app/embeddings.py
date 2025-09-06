from sentence_transformers import SentenceTransformer
from functools import lru_cache
import numpy as np
from app.config import settings


@lru_cache(maxsize=1)
def get_embedder():
    model = SentenceTransformer(settings.embed_model_name) # CPU OK
    return model
 

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vecs = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return vecs.astype(np.float32).tolist()


# Optional reranker
try:
    from sentence_transformers import CrossEncoder
except Exception:
    CrossEncoder = None


_reranker = None


def get_reranker():
    global _reranker
    if not settings.enable_reranker:
        return None
    if CrossEncoder is None:
        return None
    if _reranker is None:
        _reranker = CrossEncoder(settings.reranker_model_name)
    return _reranker