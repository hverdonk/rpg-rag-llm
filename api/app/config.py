import os
from pydantic import BaseModel


class Settings(BaseModel):
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    sessions_dir: str = os.getenv("NOTES_SESSIONS_DIR", "./sessions")
    characters_dir: str = os.getenv("NOTES_CHARACTERS_DIR", "./characters")
    embed_model_name: str = os.getenv("EMBED_MODEL_NAME", "BAAI/bge-small-en-v1.5")
    reranker_model_name: str = os.getenv("RERANKER_MODEL_NAME", "BAAI/bge-reranker-base")
    enable_reranker: bool = os.getenv("ENABLE_RERANKER", "false").lower() == "true"
    max_context_chunks: int = int(os.getenv("MAX_CONTEXT_CHUNKS", "8"))
    
    # Generator settings
    generator_provider: str = os.getenv("GENERATOR_PROVIDER", "ollama")  # "ollama" or "gemini"
    
    # Ollama settings
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model_name: str = os.getenv("OLLAMA_MODEL_NAME", "llama3.1:8b-instruct-q4_K_M")
    
    # Gemini settings
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model_name: str = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash")


settings = Settings()