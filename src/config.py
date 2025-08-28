import os
from pydantic import BaseModel

class Settings(BaseModel):
    OPENSEARCH_URL: str = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
    OPENSEARCH_USER: str = os.getenv("OPENSEARCH_USER", "admin")
    OPENSEARCH_PASS: str = os.getenv("OPENSEARCH_PASS", "admin")
    OPENSEARCH_INDEX: str = os.getenv("OPENSEARCH_INDEX", "pdf_search")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    API_KEYS: list[str] = os.getenv("API_KEYS", "devkey123").split(",")
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "pdf-search")
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    # Embeddings
    TEXT_MODEL: str = os.getenv("TEXT_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    IMAGE_MODEL: str = os.getenv("IMAGE_MODEL", "sentence-transformers/clip-ViT-B-32")
    EMBEDDING_DIM: int = int(os.getenv("EMBEDDING_DIM", 384))  # all-MiniLM-L6-v2 dim

settings = Settings()
