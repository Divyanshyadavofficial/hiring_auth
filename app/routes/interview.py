from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from datetime import datetime,timezone

from app.models import interview
from app.models_db.interview import Interview
from app.models_db.interview import InterviewFeedback
from app.models.interview import InterviewFeedbackRequest,InterviewDashboardResponse
from app.utils.dependencies import require_roles
from app.models_db.application import Application
from app.models_db.job import Job
from app.models_db.user import User
from app.services.notification_service import create_notification

interview_router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"]
)

@interview_router.get("/my",response_model=list[InterviewDashboardResponse])
async def my_interviews(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["interviewer"])
    )
):
    try:

        result = await db.execute(
            select(
                Interview,
                Application,
                User,
                Job
            )
            .join(
                Application,
                Interview.application_id == Application.id
            )
            .join(
                User,
                Application.user_id == User.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(
                Interview.interviewer_id == current_user["user_id"]
            )
            .order_by(
                Interview.scheduled_at
            )
        )
        return[
            {
                "interview_id": interview.id,
                "application_id":application.id,
                "candidate_id":candidate.id,

                "candidate_name": candidate.name,

                "candidate_email": candidate.email,
                "job_id":job.id,
                "job_title": job.title,

                "round_number": interview.round_number,

                "scheduled_at": interview.scheduled_at,

                "meeting_link": interview.meeting_link,

                "status": interview.status
            }
            for interview,application,candidate,job in result.all()
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get interviews "
            f"{str(e)}"
        )


@interview_router.get("/{interview_id}")
async def get_interview(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles([
            "admin",
            "recruiter",
            "interviewer"
        ])
    )
):
    try:
        

        result = await db.execute(
            select(
                Interview,
                Application,
                User,
                Job
            )
            .join(
                Application,
                Interview.application_id == Application.id
            )
            .join(
                User,
                Application.user_id == User.id
            )
            .join(
                Job,
                Application.job_id == Job.id
            )
            .where(
                Interview.id == interview_id
            )
        )

        row = result.one_or_none()

        if not row:
            raise HTTPException(
            status_code=404,
            detail="Interview not found"
        )

        interview, application, candidate, job = row

        if (
                current_user["role"] == "interviewer"
                and interview.interviewer_id != current_user["user_id"]
            ):
                raise HTTPException(
                status_code=403,
                detail="Not allowed"
                )
        if current_user["role"] == "recruiter":
                if job.created_by != current_user["user_id"]:
                    raise HTTPException(
                    status_code=403,
                    detail="Not allowed"
                )

        return{
            "interview_id": interview.id,

            "application_id": application.id,

            "candidate": {

                "id": candidate.id,

                "name": candidate.name,

                "email": candidate.email,

                "resume_url": candidate.resume_url

            },

            "job": {

                "id": job.id,

                "title": job.title

            },

            "round_number": interview.round_number,

            "scheduled_at": interview.scheduled_at,

            "meeting_link": interview.meeting_link,

            "status": interview.status
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch interview: {str(e)}"
        )
        


@interview_router.post(
    "/{interview_id}/feedback"
)
async def submit_feedback(
    interview_id: int,
    payload: InterviewFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(
            ["admin","recruiter"]
        )
    )

):
    try:
        interview = await db.get(
            Interview,
            interview_id
        )
        if not interview:
            raise HTTPException(
                status_code=404,
                detail="Interview not found"
            )
        if current_user["role"]!="admin" and interview.interviewer_id!=current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if interview.status == "completed":
            raise HTTPException(
                status_code=400,
                detail="Feedback already submitted"
            )
        existing_result = await db.execute(
            select(InterviewFeedback).where(
                InterviewFeedback.interview_id == interview_id
            )
        )

        existing_feedback = (
            existing_result.scalar_one_or_none()
           
        )

        if existing_feedback:
            raise HTTPException(
                status_code=400,
                detail="Feedback already exists"
            )
        overall_score = round(
            (
                payload.technical_score
                + payload.communication_score
                + payload.problem_solving_score
            ) / 3,
            2
        )
        
        feedback = InterviewFeedback(
            interview_id = interview_id,
            technical_score = payload.technical_score,
            communication_score= payload.communication_score,
            problem_solving_score = payload.problem_solving_score,
            strengths = payload.strengths,
            weaknesses= payload.weaknesses,
            recommendation=payload.recommendation,
            overall_score = overall_score
        )
        db.add(feedback)

        
        application = await db.get(
        Application,
        interview.application_id
        )

        await create_notification(
            db=db,
            user_id=application.user_id,
            event_type="INTERVIEW_COMPLETED",
            message="Interview feedback submitted."
        )


        await db.commit()

        await db.refresh(feedback)

        return {
            "message":
                "Feedback submitted successfullly",
            "feedback_id":feedback.id,
            "interview_id":interview_id,
            "overall_score":overall_score,
            "recommendation": payload.recommendation
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"failed to submit feedback: "
            f"{str(e)}"
        )
    

@interview_router.patch("/{interview_id}/start")
async def interview_start(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","interviewer"])
    )
):
    try: 
        interview = await db.get(
            Interview,
            interview_id
        )
        if not interview:
            raise HTTPException(
                status_code=404,
                detail="Interview not found"
            )
        if (
            current_user["role"] == "interviewer"
            and interview.interviewer_id !=current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if interview.status !="scheduled":
            raise HTTPException(
                status_code=400,
                detail="Interview already started or completed"
            )
        interview.status = "in_progress"
        interview.started_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(interview)
        return {
            "message":"Interview started",
            "status":interview.status,
            "started_at":interview.started_at
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start interview: {str(e)}"
        )
    


@interview_router.patch("/{interview_id}/complete")
async def interview_complete(
    interview_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["admin","interviewer"])
    )
):
    try: 
        interview = await db.get(
            Interview,
            interview_id
        )
        if not interview:
            raise HTTPException(
                status_code=404,
                detail="Interview not found"
            )
        if (
            current_user["role"] == "interviewer"
            and interview.interviewer_id != current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if interview.status != "in_progress":
            raise HTTPException(
                status_code=400,
                detail="Interview has not started"
            )
        interview.status ="completed"
        interview.completed_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(interview)

        return {
            "message": "Interview completed",
            "status": interview.status,
            "completed_at": interview.completed_at
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete interview: {str(e)}"
        )
