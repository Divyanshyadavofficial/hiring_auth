import chromadb

from functools import lru_cache


@lru_cache(maxsize=1)
def get_chroma_client():

    return chromadb.PersistentClient(
        path="./chroma_db"
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