from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from app.db import get_db
from app.models_db.application import Application
from app.models_db.job import Job
from app.models_db.job_skill import JobSkill
from app.utils.dependencies import require_roles
from app.models_db.user import User
from app.models_db.resume_skill import ResumeSkill
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
    results = []
    for app, job, user in rows:

        skills_result = await db.execute(

            select(ResumeSkill).where(

                ResumeSkill.user_id == user.id

            )

        )
        skills = [

            skill.skill_name

            for skill in skills_result.scalars().all()

        ]
        results.append({
            "application_id": app.id,
            "job_id": job.id,
            "job_title": job.title,
            "candidate_id": user.id,
            "candidate_name": user.name,
            "candidate_email": user.email,
            "resume_url": user.resume_url,
            "status": app.status,
            "match_score": app.match_score,
            "skills": skills
        })
    return {
        "page":page,
        "limit":limit,
        "results":results
    }


@dashboard_router.get("/recruiter/jobs/{job_id}/top-candidates")
async def top_candidates(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["recruiter","admin"]))
):
    job = await db.get(Job,job_id)
    if not job: 
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )
    if(
        current_user["role"]!="admin"and job.created_by!=current_user["user_id"]
    ):
        raise HTTPException(
            status_code=403,
            detail="Not allowed"
        )
    result = await db.execute(
        select(Application,User)
        .join(User,Application.user_id==User.id)
        .where(Application.job_id == job_id)
        .order_by(Application.match_score.desc())
        .limit(10)
    )
    rows = result.all()

    results = []
    for app,user in rows:
        skills_result = await db.execute(
            select(ResumeSkill).where(
                ResumeSkill.user_id == user.id
            )
        )
        skills = [
            skill.skill_name
            for skill in skills_result.scalars().all()
        ]
        results.append({
            "candidate_id": user.id,
            "candidate_name": user.name,
            "candidate_email": user.email,
            "resume_url": user.resume_url,
            "match_score": app.match_score,
            "status": app.status,
            "skills": skills
        })
    return results


@dashboard_router.get("/recruiter/job-stats/{job_id}")
async def recruiter_job_stats(
    job_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["recruiter", "admin"]))

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
        select(

            func.count(Application.id).label("total"),
            func.avg(Application.match_score).label("avg_score"),
            func.count().filter(
                Application.status == "pending"
            ).label("pending"),
            func.count().filter(
                Application.status == "accepted"
            ).label("accepted"),
            func.count().filter(
                Application.status == "rejected"
            ).label("rejected")
        ).where(Application.job_id == job_id)
    )

    stats = result.one()

    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_applications": stats.total,
        "average_match_score": round(stats.avg_score or 0, 2),
        "pending": stats.pending,
        "accepted": stats.accepted,
        "rejected": stats.rejected
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

@dashboard_router.get("/candidate/resume-status")

async def resume_status(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["candidate"]))
):
    user = await db.get(
        User,
        current_user["user_id"]

    )
    return {

        "resume_uploaded": bool(user.resume_url),
        "resume_url": user.resume_url

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
                "candidate_name": user.name,
                "candidate_email": user.email,
                "status": app.status,
                "match_score": app.match_score
            }
            for app, job,user in rows
        ]
    }