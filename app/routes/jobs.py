from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models_db.job import Job
from app.models.job import JobCreate
from app.utils.dependencies import require_roles

from app.models_db.application import Application
from app.models.applications import ApplyRequest

jobs_router = APIRouter()

@jobs_router.post("/jobs")
async def create_job(
    job: JobCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["recruiter", "admin"]))
):
    new_job = Job(
        title=job.title,
        description = job.description,
        created_by = current_user["user_id"]
    )
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)

    return {"message":"Job created","job_id":new_job.id}

from sqlalchemy import select

@jobs_router.get("/")
async def get_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Job))
    jobs = result.scalars().all()
    return jobs


@jobs_router.post("/apply")
async def apply_job(
    data: ApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["candidate"]))
):
    application = Application(
        user_id = current_user["user_id"],
        job_id=data.job_id
    )
    db.add(application)
    await db.commit()

    return {"message":"Applied successfully"}



