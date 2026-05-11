from sentence_transformers import SentenceTransformer
from functools import lru_cache


@lru_cache
def get_embedding_model():
   
    print("Loading embedding model")
    return SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )