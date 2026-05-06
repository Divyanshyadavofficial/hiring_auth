from fastapi import APIRouter,Depends,Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from app.db import get_db
from app.models_db.application import Application
from app.models_db.job import Job
from app.utils.dependencies import require_roles

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