import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.llm_service import llm

from app.models_db.application import Application
from app.models_db.job import Job
from app.models_db.user import User
from app.models_db.candidate_attempt import CandidateAttempt
from app.models_db.assessmentFeedback import AssessmentFeedback
from app.models_db.interview import Interview
from app.models_db.interview import InterviewFeedback
from fastapi import HTTPException
from app.models_db.ai_hiring_recommendation import AIHiringRecommendation

def build_hiring_prompt(
        candidate_name: str,
        job_title: str,
        match_score:float,
        assessment_percentage:float,
        assessment_passed: bool,
        assessment_feedback: str|None,
        interview_feedback: InterviewFeedback |None
):
    return f"""
    You are an expert AI hiring assistant.

    Evaluate the candidate objectively.

    Job Title:
    {job_title}

    Candidate:
    {candidate_name}

    Resume Match Score:
    {match_score}

    Assessment Percentage:
    {assessment_percentage}

    Assessment Passed:
    {assessment_passed}

    Assessment Feedback:
    {assessment_feedback}

    Interview Scores

    Technical:
    {interview_feedback.technical_score if interview_feedback else "N/A"}

    Communication:
    {interview_feedback.communication_score if interview_feedback else "N/A"}

    Problem Solving:
    {interview_feedback.problem_solving_score if interview_feedback else "N/A"}

    Interview Recommendation:
    {interview_feedback.recommendation if interview_feedback else "N/A"}

    Return ONLY valid JSON.

    {{
        "recommendation":"",
        "confidence":0,
        "summary":"",
        "reasoning":[],
        "strengths":[],
        "risks":[]
    }}
    """



async def generate_hiring_recommendation(
        application_id: int,
        db: AsyncSession
):
    try:
        application = await db.get(
            Application,
            application_id
        )
        if not application:
            raise HTTPException(
                status_code=404,
                detail="Application not found"
            )
        
        existing_result = await db.execute(
            select(AIHiringRecommendation).where(
                AIHiringRecommendation.application_id == application_id
            )
        )

        existing = existing_result.scalar_one_or_none()

        if existing:
            return existing
        
        job = await db.get(
            Job,
            application.job_id
        )
        candidate = await db.get(
            User,
            application.user_id
        )
        attempt_result = await db.execute(
            select(CandidateAttempt)
            .where(
                CandidateAttempt.application_id == application.id,
                CandidateAttempt.status =="completed"
            )
        )
        attempt = attempt_result.scalar_one_or_none()

        feedback = None

        if attempt:
            feedback_result = await db.execute(
                select(AssessmentFeedback)
                .where(
                    AssessmentFeedback.attempt_id == attempt.id
                )
            )
            feedback = feedback_result.scalar_one_or_none()

        interview_result = await db.execute(
            select(Interview)
            .where(
                Interview.application_id == application.id
            )
        )
        interview = interview_result.scalar_one_or_none()

        interview_feedback = None

        if interview:

            result = await db.execute(
                select(InterviewFeedback)
                .where(
                    InterviewFeedback.interview_id == interview.id
                )
            )

            interview_feedback = result.scalar_one_or_none()

        prompt = build_hiring_prompt(
            candidate_name=candidate.name,
            job_title=job.title,
            match_score=application.match_score,
            assessment_percentage=(
                attempt.percentage if attempt else 0
            ),
            assessment_passed=(
                attempt.passed if attempt else False
            ),
            assessment_feedback=(
                feedback.recommendation if feedback else None
            ),
            interview_feedback=interview_feedback
        )
        
        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        if content.startswith("```json"):
            content = (
                content
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        recommendation= json.loads(content)
        ai_result = AIHiringRecommendation(
            application_id=application.id,
            recommendation=recommendation["recommendation"],
            confidence=recommendation["confidence"],
            summary=recommendation["summary"],
            reasoning=recommendation["reasoning"],
            strengths=recommendation["strengths"],
            risks=recommendation["risks"]
        )

        db.add(ai_result)

        await db.commit()
        await db.refresh(ai_result)
        return ai_result
    except HTTPException:
        raise
    except json.JSONDecodeError:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail="LLM returned invalid JSON."
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"AI recommendation generation failed: {str(e)}"
        )