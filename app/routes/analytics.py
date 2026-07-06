from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func

from app.db import get_db
from app.models_db.candidate_attempt import CandidateAttempt
from app.models_db.job import Job
from app.models_db.application import Application
from app.models_db.interview import Interview, InterviewFeedback
from app.models_db.offer import Offer

from app.utils.dependencies import require_roles

analytics_router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@analytics_router.get("/dashboard")
async def recruiter_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin", "recruiter"])
    )

):
    try:
        job_filter = []

        if current_user["role"]!="admin":
            job_filter.append(
                Job.created_by == current_user["user_id"]
            )
        jobs_result = await db.execute(
            select(func.count(Job.id))
            .where(*job_filter)
        )
        total_jobs = jobs_result.scalar() or 0

        application_result = await db.execute(
            select(func.count(Application.id))
            .join(Job,Application.job_id == Job.id)
            .where(*job_filter)
        )

        total_applications = (
            application_result.scalar() or 0
        )

        shortlisted_result = await db.execute(
            select(func.count(Application.id))
            .join(Job,Application.job_id == Job.id)
            .where(
                Application.shortlist_status.in_(
                    [
                        "shortlisted",
                        "interview",
                        "hired"
                    ]
                ),
                *job_filter
            )
        )

        shortlisted = shortlisted_result.scalar() or 0

        interview_result = await db.execute(
            select(func.count(Interview.id))
            .join(
                Application,
                Interview.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*job_filter)
        )

        interviews = interview_result.scalar() or 0

        offers_result = await db.execute(
            select(func.count(Offer.id))
            .join(
                Application,
                Offer.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*job_filter)
        )
        offers = offers_result.scalar() or 0

        hires_result = await db.execute(
            select(func.count(Application.id))
            .join(Job,Application.job_id == Job.id)
            .where(
                Application.shortlist_status =="hired",
                *job_filter
            )
        )
        hires = hires_result.scalar() or 0

        return {
            "total_jobs":total_jobs,
            "total_applications": total_applications,
            "shortlisted":shortlisted,
            "interviews":interviews,
            "offers":offers,
            "hires":hires
        }
    except HTTPException:
        raise
    except Exception as e: 
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load analytics: {str(e)}"
        )


@analytics_router.get("funnel")
async def hiring_funnel(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    try:
        job_filter = []

        if current_user["role"] !="admin":
            job_filter.append(
                Job.created_by == current_user["user_id"]
            )
        applied_result = await db.execute(
            select(func.count(Application.id))
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*job_filter)
        )
        applied = applied_result.scalar() or 0

        assessment_result = await db.execute(
            select(func.count(CandidateAttempt.id))
            .join(
                Application,
                CandidateAttempt.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(
                CandidateAttempt.status == "completed",
                *job_filter
            )
        )
        assessment_completed = (
            assessment_result.scalar() or 0
        )

        shortlisted_result = await db.execute(
            select(func.count(Application.id))
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(
                Application.shortlist_status.in_(
                    [
                        "shortlisted",
                        "interview",
                        "hired"
                    ]
                ),
                *job_filter
            )
        )
        shortlisted = shortlisted_result.scalar() or 0

        interview_result = await db.execute(
            select(func.count(Interview.id))
            .join(
                Application,
                Interview.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*job_filter)
        )
        interview = interview_result.scalar() or 0

        offer_result = await db.execute(
            select(func.count(Offer.id))
            .join(
                Application,
                Offer.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*job_filter)
        )

        offer = offer_result.scalar() or 0


        hired_result = await db.execute(
            select(func.count(Application.id))
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(
                Application.shortlist_status == "hired",
                *job_filter
            )
        )

        hired = hired_result.scalar() or 0
        return{
            "applied":applied,
            "assessment_completed":assessment_completed,
            "shortlisted":shortlisted,
            "interview":interview,
            "offer":offer,
            "hired":hired
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load hiring funnel:{str(e)}"
        )

@analytics_router.get("/offers")
async def offer_analytics(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    try:
        filters = []
        if current_user["role"]!="admin":
            filters.append(
                Job.created_by == current_user["user_id"]
            )
        result = await db.execute(
            select(
                func.count(Offer.id).label("total"),
                func.count()
                .filter(
                    Offer.status =="pending"

                )
                .label("pending"),
                func.count()
                .filter(
                    Offer.status =="accepted"
                )
                .label("accepted"),
                func.count()
                .filter(
                    Offer.status =="declined"
                )
                .label("declined"),
                func.count()
                .filter(
                    Offer.status =="withdrawn"
                )
                .label("withdrawn")
            )
            .join(
                Application,
                Offer.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*filters)

        )
        stats = result.one()
        acceptance_rate = (
            round(
                (stats.accepted/stats.total)*100,
                2

            )
            if stats.total
            else 0
        )
        return {
            "total_offers": stats.total,
            "pending": stats.pending,
            "accepted": stats.accepted,
            "declined": stats.declined,
            "withdrawn": stats.withdrawn,
            "acceptance_rate": acceptance_rate
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load offer analytics: {str(e)}"
        )
    

@analytics_router.get("/assessments")
async def assessment_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin", "recruiter"])
    )
):
    try:

        filters = []

        if current_user["role"] != "admin":
            filters.append(
                Job.created_by == current_user["user_id"]
            )

        result = await db.execute(
            select(
                func.count(CandidateAttempt.id).label("total_attempts"),

                func.count()
                .filter(
                    CandidateAttempt.status == "completed"
                )
                .label("completed_attempts"),

                func.count()
                .filter(
                    CandidateAttempt.passed == True
                )
                .label("passed"),

                func.count()
                .filter(
                    CandidateAttempt.passed == False
                )
                .label("failed"),

                func.avg(
                    CandidateAttempt.percentage
                )
                .label("average_percentage"),

                func.max(
                    CandidateAttempt.percentage
                )
                .label("highest_percentage"),

                func.min(
                    CandidateAttempt.percentage
                )
                .label("lowest_percentage")
            )
            .join(
                Application,
                CandidateAttempt.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(*filters)
        )

        stats = result.one()

        return {
            "total_attempts": stats.total_attempts,
            "completed_attempts": stats.completed_attempts,
            "passed": stats.passed,
            "failed": stats.failed,
            "average_percentage": round(
                stats.average_percentage or 0,
                2
            ),
            "highest_percentage": round(
                stats.highest_percentage or 0,
                2
            ),
            "lowest_percentage": round(
                stats.lowest_percentage or 0,
                2
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load assessment analytics: {str(e)}"
        )
    

@analytics_router.get("/interviews")
async def interview_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(
        require_roles(["admin", "recruiter"])
    )
):
    try:

        filters = []

        if current_user["role"] != "admin":
            filters.append(
                Job.created_by == current_user["user_id"]
            )

        result = await db.execute(
            select(
                func.count(Interview.id).label("total_interviews"),

                func.count()
                .filter(
                    Interview.status == "scheduled"
                )
                .label("scheduled"),

                func.count()
                .filter(
                    Interview.status == "completed"
                )
                .label("completed"),

                func.count()
                .filter(
                    Interview.status == "cancelled"
                )
                .label("cancelled"),

                func.avg(
                    InterviewFeedback.overall_rating
                )
                .label("average_rating")
            )
            .join(
                Application,
                Interview.application_id == Application.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .outerjoin(
                InterviewFeedback,
                Interview.id == InterviewFeedback.interview_id
            )
            .where(*filters)
        )

        stats = result.one()

        return {
            "total_interviews": stats.total_interviews,
            "scheduled": stats.scheduled,
            "completed": stats.completed,
            "cancelled": stats.cancelled,
            "average_rating": round(
                stats.average_rating or 0,
                2
            )
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load interview analytics: {str(e)}"
        )