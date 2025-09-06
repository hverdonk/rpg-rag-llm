from app.config import settings
import weaviate


_client = None


def get_client() -> weaviate.WeaviateClient:
    global _client
    if _client is None:
        _client = weaviate.connect_to_local(
            host=settings.weaviate_url.replace("http://", "").split(":")[0],
            port=int(settings.weaviate_url.split(":")[-1])
        )
    return _client

# 'path' is file path, in this case
SCHEMA = {
    "classes": [
        {
            "class": "Character",
            "vectorizer": "none",
            "properties": [
                {"name": "name", "dataType": ["text"]},
                {"name": "aliases", "dataType": ["text[]"]},
                {"name": "path", "dataType": ["text"]}
            ]
        },
        {
            "class": "Document",
            "vectorizer": "none",
            "properties": [
                {"name": "type", "dataType": ["text"]},
                {"name": "title", "dataType": ["text"]},
                {"name": "sessionNo", "dataType": ["int"]},
                {"name": "sessionDate", "dataType": ["date"]},
                {"name": "path", "dataType": ["text"]},
                {"name": "links", "dataType": ["Document"]}
            ]
        },
        {
            "class": "Chunk",
            "vectorizer": "none",
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "heading", "dataType": ["text"]},
                {"name": "startChar", "dataType": ["int"]},
                {"name": "endChar", "dataType": ["int"]},
                {"name": "sessionNo", "dataType": ["int"]},
                {"name": "sessionDate", "dataType": ["date"]},
                {"name": "ofDoc", "dataType": ["Document"]},
                {"name": "characters", "dataType": ["Character"]}
            ]
        }
    ]
}


def ensure_schema():
    client = get_client()
    with client.batch.configure(batch_size=200):
        existing = {c["class"] for c in client.schema.get()["classes"]}
        for cls in SCHEMA["classes"]:
            if cls["class"] not in existing:
                client.schema.create_class(cls)