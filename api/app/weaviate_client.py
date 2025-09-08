from app.config import settings
import weaviate
from weaviate.classes.config import Configure, Property, DataType, ReferenceProperty, VectorDistances


_client = None


def get_client() -> weaviate.WeaviateClient:
    global _client
    if _client is None:
        _client = weaviate.connect_to_local(
            host=settings.weaviate_url.replace("http://", "").split(":")[0],
            port=int(settings.weaviate_url.split(":")[-1])
        )
    return _client



def ensure_schema():
    client = get_client()
    existing_collections = set(client.collections.list_all().keys())
    
    # Create Character collection
    if "Character" not in existing_collections:
        client.collections.create(
            name="Character",
            properties=[
                Property(name="name", data_type=DataType.TEXT),
                Property(name="aliases", data_type=DataType.TEXT_ARRAY),
                Property(name="path", data_type=DataType.TEXT)
            ]
        )
    
    # Create Location collection
    if "Location" not in existing_collections:
        client.collections.create(
            name="Location",
            properties=[
                Property(name="name", data_type=DataType.TEXT),
                Property(name="aliases", data_type=DataType.TEXT_ARRAY),
                Property(name="path", data_type=DataType.TEXT)
            ]
        )
    
    # Create Organization collection
    if "Organization" not in existing_collections:
        client.collections.create(
            name="Organization",
            properties=[
                Property(name="name", data_type=DataType.TEXT),
                Property(name="aliases", data_type=DataType.TEXT_ARRAY),
                Property(name="path", data_type=DataType.TEXT)
            ]
        )
    
    # Create Document collection
    if "Document" not in existing_collections:
        client.collections.create(
            name="Document",
            properties=[
                Property(name="type", data_type=DataType.TEXT),
                Property(name="title", data_type=DataType.TEXT),
                Property(name="sessionNo", data_type=DataType.INT),
                Property(name="sessionDate", data_type=DataType.DATE),
                Property(name="path", data_type=DataType.TEXT)
            ]
        )
    
    # Create Chunk collection with references and vector config
    if "Chunk" not in existing_collections:
        client.collections.create(
            name="Chunk",
            properties=[
                Property(name="text", data_type=DataType.TEXT),
                Property(name="heading", data_type=DataType.TEXT),
                Property(name="startChar", data_type=DataType.INT),
                Property(name="endChar", data_type=DataType.INT),
                Property(name="sessionNo", data_type=DataType.INT),
                Property(name="sessionDate", data_type=DataType.DATE)
            ],
            references=[
                ReferenceProperty(name="ofDoc", target_collection="Document"),
                ReferenceProperty(name="characters", target_collection="Character"),
                ReferenceProperty(name="locations", target_collection="Location"),
                ReferenceProperty(name="organizations", target_collection="Organization")
            ],
            vector_config=Configure.Vectors.self_provided(
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE
                )
            )
        )