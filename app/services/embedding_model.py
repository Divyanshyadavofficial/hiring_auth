from sentence_transformers import SentenceTransformer
from functools import lru_cache

from app.core.config import get_settings
settings = get_settings()
@lru_cache
def get_embedding_model():
   
    print("Loading embedding model")
    return SentenceTransformer(
            settings.EMBEDDING_MODEL
        )