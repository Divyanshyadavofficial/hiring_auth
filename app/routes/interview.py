from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

from app.models_db.interview import Interview
from app.models_db.interview import InterviewFeedback
from app.models.interview import InterviewFeedbackRequest
from app.utils.dependencies import require_roles

interview_router = APIRouter(
    prefix="/interviews",
    tags=["Interviews"]
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

        interview.status = "completed"

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