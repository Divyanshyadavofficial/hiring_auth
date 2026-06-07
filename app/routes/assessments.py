from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assessment import SubmitAnswerRequest
from app.models_db.assessment_question import AssessmentQuestion
from app.models_db.AssessmentBlueprint import Assessment,AssessmentBlueprint
from app.models_db.job import Job
from app.models_db.application import Application
from app.models_db.candidate_attempt import CandidateAttempt
from app.models_db.CandidateAnswer import CandidateAnswer
from app.db import get_db
from app.utils.dependencies import require_roles
from app.models.question_review import QuestionReviewRequest
from app.models.question_validation import QuestionSchema
from app.services.llm_service import llm
import json
from datetime import datetime

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
async def assessment_start(
        assessment_id: int,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(require_roles(["candidate"]))
):
    try:
        assessment = await db.get(Assessment,
                                  assessment_id)
        if not assessment:
            raise HTTPException(status_code=404,detail="Assessment does not exists")
        
        if assessment.status != "published":
            raise HTTPException(
                status_code=400,
                detail="Assessment is not published yet"
            )
        
        result = await db.execute(
            select(Application).where(
                Application.user_id == current_user["user_id"],
                Application.job_id == assessment.job_id
            )
        )

        application = result.scalar_one_or_none()
        
        if not application:
            raise HTTPException(
                status_code=403,
                detail=("You have not applied for this job")
            )
        
        existing_attempt_result = await db.execute(
            select(CandidateAttempt).where(
                CandidateAttempt.application_id == application.id,
                CandidateAttempt.assessment_id == assessment_id
            )
        )

        existing_attempt = existing_attempt_result.scalar_one_or_none()

        if existing_attempt:
            raise HTTPException(
                status_code=400,
                detail="Assessment attempt already exists"
            )
        
        new_attempt = CandidateAttempt(
            application_id = application.id,
            assessment_id = assessment.id,
            status = "in_progress"
        )
        db.add(new_attempt)

        await db.commit()
        await db.refresh(new_attempt)
        return {
            "message":(
                "Assessment started successfully"
            ),
            "attempt_id":new_attempt.id,
            "assessment_id":assessment_id,
            "status":new_attempt.status
        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Assessment start failed: "
            f"{str(e)}"
        )



@assessment_router.get("/attempts/{attempt_id}/next-question")
async def get_next_question(
        attempt_id: int,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(
            require_roles(["candidate"])
        )
):
    try:
        attempt = await db.get(CandidateAttempt,attempt_id)
        if not attempt:
            raise HTTPException(status_code=404,detail="Attempt not found")
        
        application = await db.get(
            Application,
            attempt.application_id
        )
        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        if application.user_id!=current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if attempt.status!="in_progress":
            raise HTTPException(
                status_code=400,
                detail="Attempt is no longer active"
            )

        answered_result = await db.execute(
            select(
                CandidateAnswer.question_id
            ).where(
                CandidateAnswer.attempt_id == attempt_id
            )
        )
        answered_ids = set(
            answered_result.scalars().all()
        )

        question_result = await db.execute(
            select(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == attempt.assessment_id
            )
            .order_by(
                AssessmentQuestion.id
            )
        )
        questions = question_result.scalars().all()

        next_question = None
        for question in questions:
            if question.id not in answered_ids:
                next_question = question
                break
        
        if not next_question:
            return{
                "completed":True,
                "message":(
                    "All questions attempted. "
                    "Please finish assessment"
                )
            }
        return {
            "completed":False,
            "question":{
                "id":next_question.id,
                "skill_name":next_question.skill_name,
                "question_type":next_question.question_type,
                "difficulty_level":next_question.difficulty_level,
                "question_text":next_question.question_text,
                "options":next_question.options,
                "marks":next_question.marks,
                "time_limit_seconds":next_question.time_limit_seconds
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                f"failed to fetch next question: "
                f"{str(e)}"
            )
        )
    

@assessment_router.post("/attempts/questions/{question_id}/submit")
async def question_submit(
        question_id : int,
        attempt_id: int,
        payload: SubmitAnswerRequest,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(require_roles(["candidate"]))
        
):
    try: 
        attempt = await db.get(CandidateAttempt,attempt_id)
        if not attempt:
            raise HTTPException(status_code=404,
                            detail="Attempt not found")
        
        if attempt.status!="in_progress":
            raise HTTPException(
                status_code=400,
                detail="Attempt is not active"
            )
        
        application = await db.get(
            Application,
            attempt.application_id 
        )

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application mot found"
            )
        

        if application.user_id!=current_user["user_id"]:
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        
        
        question = await db.get(
            AssessmentQuestion,question_id
        )
        if not question:
            raise HTTPException(status_code=404,
                detail="question not found")
        
        if question.assessment_id !=attempt.assessment_id:
            raise HTTPException(
                status_code=400,
                detail="Question does not belong to this assessment"
            )
        
        

        existing_anser_result = await db.execute(
            select(CandidateAnswer).where(
                CandidateAnswer.attempt_id == attempt.id,
                CandidateAnswer.question_id == question_id
            )
        )

        existing_answer = existing_anser_result.scalar_one_or_none()

        if existing_answer:
            raise HTTPException(
                status_code=400,
                detail= "Question already answered"
            )
        
        is_correct = (
            payload.answer.strip().lower() 
            ==
            question.expected_answer.strip().lower()
        )

        obtained_marks = (
            question.marks
            if is_correct
            else 0
        )

        candidate_answer = CandidateAnswer(
            attempt_id = attempt.id,
            question_id = question.id,
            candidate_answer = payload.answer,
            is_correct=is_correct,
            obtained_marks=obtained_marks,
            time_taken_seconds=payload.time_taken_seconds
        )
        db.add(candidate_answer)

        await db.commit()

        return{
            "message":
                "Answer submitted successfully",
            "question_id": question.id,
            "is_correct":is_correct,
            "obtained_marks":obtained_marks
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Answer submission failed: "
            f"{str(e)}"
        )
    

@assessment_router.post(
        "/attempts/{attempt_id/finish}"
)
async def finish_assessment(
    attempt_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["candidate"])
    )

):
    try:
        attempt = await db.get(
            CandidateAttempt,
            attempt_id
        )
        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Attempt not found"
            )
        
        application = await db.get(
            Application,
            attempt.application_id
        )

        if not application:
            raise HTTPException(
                status_code=404,
                detail= "Application not found"
            )
        if(
            application.user_id!=current_user["user_id"]
        ):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if attempt.status !="in_progress":
            raise HTTPException(
                status_code=400,
                detail="Assessment already completed"
            )
        score_result = await db.execute(
            select(
                func.sum(
                    CandidateAnswer.obtained_marks
                ).where(
                    CandidateAnswer.attempt_id == attempt_id
                )
            )
        )
        total_score = score_result.scalar() or 0

        marks_result = await db.execute(
            select(
                func.sum(
                    AssessmentQuestion.marks
                )
            ).where(
                AssessmentQuestion.assessment_id == attempt.assessment_id
            )
        )
        
        total_possible_marks = marks_result.scalar() or 0

        if total_possible_marks ==0:
            raise HTTPException(
                status_code=400,
                detail="Assessment has no marks"
            )
        
        percentage = round(
            (
                total_score/total_possible_marks
            )*100,
            2
        )

        assessment = await db.get(
            Assessment,
            attempt.assessment_id
        )

        if not assessment:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
            )
        blueprint = await db.get(
            AssessmentBlueprint,
            assessment.blueprint_id
        )

        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found"
            )
        
        passed = percentage>=blueprint.passing_score_percentage
        attempt.total_score = total_score
        attempt.percentage = percentage
        attempt.passed = passed
        attempt.completed_at = datetime.utcnow()
        attempt.status = "completed"
        await db.commit()

        return {
            "message":
                "Assessment completed successfully",
            "attempt_id":
                attempt_id,
            "total_score":
                total_score,
            "total_possible_marks":
                total_possible_marks,
            "percentage":
                percentage,
            "passing_score":
                blueprint.passing_score_percentage,
            "passed":
            attempt.passed
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to finish assessment: "
                f"{str(e)}"
            )
        )
    

@assessment_router.get("/attempts/{attempt_id}/result")
async def get_attempt_result(
    attempt_id:int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(
        require_roles(["candidate"])
    )
):
    try:
        attempt = await db.get(
            CandidateAttempt,
            attempt_id
        )
        if not attempt:
            raise HTTPException(
                status_code=404,
                detail="Attempt not found"
            )
        application = await db.get(
            Application,
            attempt.application_id
        )

        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        if(application.user_id != current_user["user_id"]):
            raise HTTPException(
                status_code=403,
                detail="Not allowed"
            )
        if attempt.status!="completed":
            raise HTTPException(
                status_code=400,
                detail="Assessment not completed yet"
            )
        result = await db.execute(

        select(CandidateAnswer).where(

            CandidateAnswer.attempt_id == attempt.id

        )

        )

        answers = result.scalars().all()

        correct_answers = sum(

            1

                for answer in answers

                if answer.is_correct

        )

        total_attempted = len(answers)
        assessment = await db.get(
            Assessment,
            attempt.assessment_id
        )
        if not assessment:
            raise HTTPException(
                status_code=404,
                detail="Assessment not found"
        )
        blueprint = await db.get(
            AssessmentBlueprint,
            assessment.blueprint_id
        )
        if not blueprint:
            raise HTTPException(
                status_code=404,
                detail="Blueprint not found"
            )
        questions_result = await db.execute(
            select(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id
            == attempt.assessment_id
            )
        )

        total_questions = len(
        questions_result.scalars().all()
        )

        return {
            "attempt_id": attempt.id,
            "assessment_id": attempt.assessment_id,
            "total_score": attempt.total_score,
            "percentage": attempt.percentage,
            "passing_score":
                blueprint.passing_score_percentage,
            "passed": attempt.passed,
            "total_questions":total_questions,
            "questions_attempted": total_attempted,
            "correct_answers":correct_answers,
            "incorrect_answers":total_attempted - correct_answers,
            "started_at": attempt.started_at,
            "completed_at": attempt.completed_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch result: {str(e)}"
        )


