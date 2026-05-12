from fastapi import HTTPException
from app.vector_db.chroma_client import (
    get_resume_collection,
    get_job_collection
)
from app.services.similarity_service import (
    cosine_similarity
)


resume_collection = get_resume_collection()

job_collection = get_job_collection()


def calculate_match_score(
    user_id: int,
    job_id: int
):
    resume_data = resume_collection.get(
        ids=[str(user_id)],
        include=["embeddings"]
    )

    if("embeddings"not in resume_data
       or len(resume_data["embeddings"])==0):

        raise HTTPException(
            status_code=400,
            detail="please upload your resume before applying"
        )

    job_data = job_collection.get(
        ids=[str(job_id)],
        include=["embeddings"]
    )

    if (
    "embeddings" not in job_data
    or len(job_data["embeddings"]) == 0
    ):
        raise HTTPException(
        status_code=400,
        detail="Job embedding not found")
    

    resume_embedding = (
        resume_data["embeddings"][0]
    )

    job_embedding = (
        job_data["embeddings"][0]
    )

    score = cosine_similarity(
        resume_embedding,
        job_embedding
    )

    return round(score * 100, 2)