import chromadb

client = chromadb.PersistentClient(
    path="./chroma_db"
)

resume_collection = client.get_or_create_collection(

    name="resume_embeddings"

)

job_collection = client.get_or_create_collection(

    name="job_embeddings"

)