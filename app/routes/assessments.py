from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db.assessment_question import AssessmentQuestion
from app.models_db.AssessmentBlueprint import Assessment
from app.models_db.job import Job
from app.db import get_db
from app.utils.dependencies import require_roles
from app.models.question_review import QuestionReviewRequest

assessment_router = APIRouter(
    prefix="/assessments",
    tags=["Assessments"]
)

@assessment_router.get("/{assessment_id}/questions")
async def get_assessment_questions(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_roles(["recruiter","admin"]))
):
    try:
        assessment = await db.get(
            Assessment,assessment_id
        )
        if not assessment:
            raise HTTPException(status_code=404,
                                detail="Assessment not found")
        
        job = await db.get(
            Job,
            assessment.job_id
        )

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        if(current_user["role"]!="admin"
           and job.created_by!=current_user["user_id"]):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        result = await db.execute(
            select(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == assessment_id
            )
        )

        questions = result.scalars().all()

        return {

            "assessment_id": assessment.id,
            "assessment_status": assessment.status,
            "total_questions": len(questions),
            "questions": [
                {
                    "id": question.id,
                    "skill_name": question.skill_name,
                    "question_type": question.question_type,
                    "difficulty_level": (
                        question.difficulty_level
                    ),
                    "question_text": (
                        question.question_text
                    ),
                    "options": question.options,
                    "expected_answer": (
                        question.expected_answer
                    ),
                    "marks": question.marks,
                    "time_limit_seconds": (
                        question.time_limit_seconds
                    ),
                    "status": question.status,
                    "recruiter_feedback": (
                        question.recruiter_feedback
                    )
                }
                for question in questions

            ]
        }
    except HTTPException:
        raise 
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Assessment questions "
                f"fetch failed: {str(e)}"
            )
        )


@assessment_router.patch("/questions/{question_id}/review")
async def review_question(
    question_id: int,
    payload: QuestionReviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["recruiter","admin"])
    )
):
    try:
        question = await db.get(
            AssessmentQuestion,
            question_id
        )
        if not question:
            raise HTTPException(
                status_code=404,
                detail= "Question not found"
            )
        
        assessment = await db.get(
            Assessment,
            question.assessment_id
        )

        if not assessment: 
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
            )
        
        job = await db.get(
            Job,
            assessment.job_id
        )

        if not job: 
            raise HTTPException(
                status_code=404,
                detail= "Job not found"
            )
        
        if(current_user["role"]!="admin"
            and  job.created_by!= current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        allowed_statuses = [
            "approved",
            "rejected",
            "need_changes"
        ]

        if payload.status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid status"
            )
        
        question.status = payload.status

        if payload.recruiter_feedback:
            question.recruiter_feedback = payload.recruiter_feedback
        
        if payload.question_text:
            question.question_text = payload.question_text
        
        if payload.difficulty_level:
            question.difficulty_level = payload.difficulty_level

        if payload.marks is not None:
            question.marks = payload.marks
        
        if payload.time_limit_seconds is not None:
            question.time_limit_seconds = payload.time_limit_seconds
        
        if payload.expected_answer:
            question.expected_answer = payload.expected_answer
        
        if payload.options:
            question.options = payload.options
        
        await db.commit()

        await db.refresh(question)

        return{
            "message":"Question reviewed successfully",
            "question_id":question_id,
            "status":question.status
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Question review failed: "
                f"{str(e)}"
            )
        )
            
