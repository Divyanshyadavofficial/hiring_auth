from fastapi import APIRouter,Depends,HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select
from app.db import get_db
from app.models_db.job import Job
from app.models_db.user import User
from app.models_db.application import Application
from app.models.job import   JobCreate,JobResponse,JobCreateResponse,ApplyJobResponse,JobApplicationResponse


from app.utils.dependencies import require_roles

from app.services.embedding_service import generate_embedding

from app.services.skill_extractor import extract_skills 

from app.services.matching_service import calculate_match_score

from app.vector_db.chroma_client import get_job_collection

jobs_router = APIRouter( prefix="/jobs",tags=["Jobs"])


@jobs_router.post("/",response_model=JobCreateResponse)

async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(
            ["recruiter", "admin"]
        )
    )
):
    skills = extract_skills(
        job.description
    )
    embedding = generate_embedding(
        job.description
    )
    new_job = Job(
        title=job.title,
        description=job.description,
        created_by=current_user["user_id"]
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    job_collection = (
        get_job_collection()
    )
    job_collection.upsert(
        ids=[str(new_job.id)],
        embeddings=[embedding],
        documents=[job.description],
        metadatas=[
            {
                "job_id": new_job.id,
                "title": new_job.title,
                "skills": ",".join(skills)
            }
        ]
    )
    return {
        "message": "Job created",
        "job_id": new_job.id,
        "skills": skills,
    }

@jobs_router.get("/",response_model=list[JobResponse])
async def get_jobs(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Job)
    )
    jobs = result.scalars().all()
    return jobs
@jobs_router.post("/{job_id}/apply",response_model=ApplyJobResponse)

async def apply_job(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))

):

    job = await db.get(Job,job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    result = await db.execute(
        select(Application).where(
            Application.user_id== current_user["user_id"],
            Application.job_id== job_id
        )
    )

    existing = (result.scalar_one_or_none())

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Already applied"
        )

    score = calculate_match_score(
        current_user["user_id"],
        job_id
    )
    application = Application(
        user_id=current_user["user_id"],
        job_id=job_id,
        status="pending",
        match_score=score
    )
    db.add(application)
    await db.commit()
    return {
        "message": "Applied successfully",
        "match_score": score
    }


@jobs_router.get("/{job_id}/applications",response_model=list[JobApplicationResponse]
)
async def get_job_applications(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["admin", "recruiter"]))
):
    job = await db.get(Job, job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if (
        current_user["role"] != "admin"
        and job.created_by != current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )

    result = await db.execute(
        select(Application, User)
        .join(User, Application.user_id == User.id)
        .where(Application.job_id == job_id)
        .order_by(
            Application.match_score.desc()
        )
    )

    data = [
        {
            "application_id": app.id,
            "status": app.status,
            "candidate_name": user.name,
            "candidate_email": user.email,
            "match_score":app.match_score,
            "resume_url":user.resume_url
        }
        for app, user in result.all()
    ]

    return data