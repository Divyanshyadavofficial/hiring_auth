from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models_db.assessment_question import AssessmentQuestion
from app.models_db.AssessmentBlueprint import Assessment
from app.models_db.job import Job
from app.db import get_db
from app.utils.dependencies import require_roles
from app.models.question_review import QuestionReviewRequest
from app.models.question_validation import QuestionSchema
from app.services.llm_service import llm
import json

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

def question_regenerate_prompt(
        old_question,
        recruiter_feedback
):
    return  f"""
    You are an AI technical assessment generator.
    the recruiter rejected the following question.
    OLD QUESTION:
    {old_question.question_text}

    QUESTION_TYPE:
    {old_question.question_type}
    SKILL:
    {old_question.skill_name}
    CURRENT DIFFICULTY:
    {old_question.difficulty_level}
    RECRUITER FEEDBACK:
    {recruiter_feedback}
    Generate an improved replacement question.
    Return ONLY valid JSON.

    Format:
    {{
        "question_type":"",
        "difficulty_level":"",
        "question_text":"",
        "options":"{{}}",
        "correct_answer":"",
        "marks":"5",
        "time_limit_seconds":60
    }}
    """

@assessment_router.post("/questions/{question_id}/regenerate")
async def regenerate(
    question_id: int,
    db: AsyncSession = Depends(get_db),
    current_user= Depends(require_roles(["recruiter","admin"]))
):
    try:
        question = await db.get(
            AssessmentQuestion,
            question_id
        )
        if not question:
            raise HTTPException(
                status_code=404,
                detail="Question not found"
            )
        
        assessment = await db.get(
            Assessment,
            question.assessment_id
        )

        if not assessment:
            raise HTTPException(
                status_code=404,
                detail= "Assessment not found"
            )
        
        job = await db.get(
            Job,
            assessment.job_id
        )

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found"
            )
        
        if(current_user["role"]!="admin" and job.created_by!=current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if not question.recruiter_feedback:
            raise HTTPException(
                status_code=400,
                detail="Recruiter feedback required for " \
                "regeneration"
            )
        
        prompt = question_regenerate_prompt(
            old_question=question,
            recruiter_feedback=question.recruiter_feedback 
        )
        
        response = await llm.ainvoke(prompt)

        content = response.content.rstrip()

        if content.startswith("```json"):
            content = (
                content
                .replace("```json","")
                .replace("```","")
                .rstrip()
            )
        try:
            generated_question = json.loads(
                content
            )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail=(
                    "LLM returned invalid JSON"
                )
            )
        try:
            validated_question = QuestionSchema(
                **generated_question
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Question validation failed: "
                f"{str(e)}"
            )
        
        question.question_type = validated_question.question_type
        question.difficulty_level = validated_question.difficulty_level
        question.question_text = validated_question.question_text
        question.options = validated_question.options
        question.expected_answer = validated_question.correct_answer
        question.marks = validated_question.marks
        question.time_limit_seconds = validated_question.time_limit_seconds

        question.status = "pending_review"

        await db.commit()
        await db.refresh(question)

        return{
            "message":(
                "Question regenerated successfully"
            ),
            "question_id": question.id,
            "status":question.status
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Question regeneration failed: "
            f"{str(e)}"
        )


@assessment_router.post("/{assessment_id}/publish")
async def  assessment_publish(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["recruiter","admin"]))

):
    try: 
        assessment = await db.get(
            Assessment,
            assessment_id

        )
        if not assessment:
            raise HTTPException(
                status_code= 404,
                detail="Assessment not found"
            )
        
        job = await db.get(
            Job,
            assessment.job_id
        )
        if not job:
            raise HTTPException(
                status_code= 404,
                detail="Job not found"
            )
        if(current_user["role"]!="admin"and job.created_by!=
           current_user["user_id"]):
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

        if not questions:
            raise HTTPException(
                status_code=400,
                detail="Assessment has no questions"
            )
        
        not_approved = [
            question
            for question in questions
            if question.status!="approved"
        ]

        if not_approved:
            raise HTTPException(
                status_code=400,
                detail="All questions must be approved before" \
                "publishing"
            )
        
        assessment.status = "published"

        await db.commit()
        await db.refresh(assessment)
        return {
            "message":"Assessment published successfully",
            "assessment_id":assessment_id,
            "status":assessment.status
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Assessment publish failed: "
            f"{str(e)}"
        )



assessment_router.post("/{assessment_id}/start")
