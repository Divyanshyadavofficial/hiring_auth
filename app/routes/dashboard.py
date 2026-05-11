from fastapi import APIRouter,Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from app.db import get_db
from app.models_db.application import Application
from app.models_db.job import Job
from app.utils.dependencies import require_roles
from app.models_db.user import User

dashboard_router = APIRouter(prefix="/dashboard",tags=["Dashboard"])

@dashboard_router.get("/recruiter/jobs")
async def get_my_jobs(
    page: int = Query(1,ge=1),
    limit:int = Query(10,le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["recruiter","admin"]))

):
    offset = (page -1)*limit
    result = await db.execute(
        select(Job).where(Job.created_by == current_user["user_id"])
        .offset(offset)
        .limit(limit)
    )
    jobs = result.scalars().all()
    return {
        "page": page,
        "limit":limit,
        "result":jobs
    }


@dashboard_router.get("/recruiter/applications")
async def get_my_applications(
    page: int = Query(1,ge=1),
    limit: int = Query(10,le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["recruiter","admin"]))
):
    offset = (page-1)*limit

    result = await db.execute(
        select(
            Application,
            Job,
            User
        )
        .join(
            Job,
            Application.job_id==Job.id
        )
        .join(
            User,
            Application.user_id == User.id
        )
        .where(
            Job.created_by == current_user["user_id"]
        )
        .order_by(
            Application.match_score.desc()
        )
        .offset(offset)
        .limit(limit)
    )
    rows = result.all()
    return {
        "page":page,
        "limit":limit,
        "results":[
            {
                "application_id":app.id,
                "job_id": job.id,
                "job_title": job.title,
                "candidate_id": user.id,
                "candidate_name": user.name,
                "candidate_email": user.email,
                "resume_url": user.resume_url,
                "status": app.status,
                "match_score": app.match_score
            }
            for app,job,user in rows
        ]
    }


@dashboard_router.get("/candidate")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["candidate"]))
):
    user_id = current_user["user_id"]

    result = await db.execute(
        select(
            func.count().label("total"),
            func.count().filter(Application.status == "pending").label("pending"),
            func.count().filter(Application.status == "accepted").label("accepted"),
            func.count().filter(Application.status == "rejected").label("rejected"),
        ).where(Application.user_id == user_id)
    )

    stats = result.one()

    return {
        "total": stats.total,
        "pending": stats.pending,
        "accepted": stats.accepted,
        "rejected": stats.rejected
    }


@dashboard_router.get("/admin/overview")
async def admin_overview(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    total_jobs = await db.execute(select(func.count(Job.id)))
    total_applications = await db.execute(select(func.count(Application.id)))

    return {
        "total_jobs":total_jobs.scalar(),
        "total_applications":total_applications.scalar()
    }


@dashboard_router.get("/admin/applications")
async def get_all_applications(
    status: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    offset = (page - 1) * limit

    query = select(Application, Job).join(Job)

    if status:
        query = query.where(Application.status == status)

    result = await db.execute(
        query.offset(offset).limit(limit)
    )

    rows = result.all()

    return {
        "page": page,
        "limit": limit,
        "results": [
            {
                "application_id": app.id,
                "job_id": job.id,
                "job_title": job.title,
                "candidate_id": app.user_id,
                "status": app.status
            }
            for app, job in rows
        ]
    }