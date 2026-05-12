import chromadb
from app.core.config import (
    get_settings
)

from functools import lru_cache


@lru_cache(maxsize=1)
def get_chroma_client():
    settings = get_settings()
    return chromadb.PersistentClient(
        path=settings.CHROMA_DB_PATH
    )


@lru_cache(maxsize=1)
def get_resume_collection():

    client = get_chroma_client()

    return client.get_or_create_collection(
        name="resume_embeddings"
    )


@lru_cache(maxsize=1)
def get_job_collection():

    client = get_chroma_client()

    return client.get_or_create_collection(
        name="job_embeddings"
    )