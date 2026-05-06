from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func

from app.db import get_db
from app.models_db.application import Application
from app.models_db.job import Job
from app.models_db.user import User

from app.utils.dependencies import require_roles,get_current_user

applications_router = APIRouter(prefix="/applications",tags=["Applications"])

@applications_router.get("/me")
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["candidate"]))
):
    result = await db.execute(
        select(Application,Job)
        .join(Job,Application.job_id==Job.id)
        .where(Application.user_id == current_user["user_id"])
    )
    return[
        {
            "application_id":app.id,
            "job_title":job.title,
            "status":app.status
        }
        for app,job in result.all()
    ]





VALID_STATUS = ["pending", "accepted", "rejected"]

@applications_router.patch("/{application_id}")
async def update_application_status(
    application_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["admin", "recruiter"]))
):
    app = await db.get(Application, application_id)

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

   
    if status not in VALID_STATUS:
        raise HTTPException(status_code=400, detail="Invalid status")

    
    job = await db.get(Job, app.job_id)

    if current_user["role"] != "admin" and job.recruiter_id != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Not allowed")

    app.status = status
    await db.commit()

    return {"message": "Status updated"}


@applications_router.get("/")
async def get_all_applications(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    result = await db.execute(
        select(Application, User, Job)
        .join(User, Application.user_id == User.id)
        .join(Job, Application.job_id == Job.id)
    )

    return [
        {
            "application_id": app.id,
            "candidate": user.name,
            "job": job.title,
            "status": app.status
        }
        for app, user, job in result.all()
    ]