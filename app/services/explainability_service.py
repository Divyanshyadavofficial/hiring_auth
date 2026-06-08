import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models_db.candidate_attempt import CandidateAttempt
from app.models_db.CandidateAnswer import CandidateAnswer
from app.models_db.assessment_question import AssessmentQuestion
from app.models_db.assessmentFeedback import AssessmentFeedback
from app.models.Assessment_feedback import (

    AssessmentFeedbackSchema

)

from app.services.llm_service import llm

def build_explainablity_prompt(
        performance_data:str
):
    return f"""
    You are an expert technical interviewer.
    Analyze the candidate performance.
    Return only valid JSON.

    

    Format:

    {{

        "strengths": [],
        "weaknesses": [],
        "recommendation": "",
        "overall_summary": "",
        "confidence_score": 0.0
    }}

    Performance Data:

    {performance_data}
    """

async def generate_assessment_feedback(
        attempt_id: int,
        db: AsyncSession
): 
    attempt = await db.get(
        CandidateAttempt,attempt_id
    )
    if not attempt:
        raise Exception("Attempt not found")
    
    existing_result = await db.execute(
        select(
            AssessmentFeedback
        ).where(
            AssessmentFeedback.attempt_id == attempt_id
        )
    )

    existing_feedback = existing_result.scalar_one_or_none()

    if existing_feedback:
        return existing_feedback
    
    result = await db.execute(
        select(
            CandidateAnswer,
            AssessmentQuestion
        )
        .join(
            AssessmentQuestion,
            CandidateAnswer.question_id
            == AssessmentQuestion.id
        )
        .where(
            CandidateAnswer.attempt_id == attempt_id
        )
    )

    rows = result.all()

    if not rows:
        raise Exception(
            "No answers found"
        )
    
    performance_data = []

    for answer,question in rows:
        performance_data.append(
            {
                "skill":question.skill_name,
                "question":question.question_text,
                "candidate_answer":answer.candidate_answer,
                "expected_answer":question.expected_answer,
                "is_correct":answer.is_correct,
                "marks_awarded":answer.obtained_marks,
                "max_marks":question.marks

            }
        )

    prompt = build_explainablity_prompt(
        json.dumps(
            performance_data,
            indent=2
        )
    )

    response = await llm.ainvoke(
        prompt
    )

    try:
        feedback_data = json.loads(
            response.content
        )
        validated = AssessmentFeedbackSchema(
            **feedback_data
        )
    except Exception as e:
        raise Exception(
            f"Invalid LLM response:{str(e)}"
        )
    
    
    
    feedback_record = (
        AssessmentFeedback(
            attempt_id=attempt_id,
            strengths=
                validated.strengths,
            weaknesses=
                validated.weaknesses,
            recommendation=
                validated.recommendation,
            overall_summary=
                validated.overall_summary,
            confidence_score=
                validated.confidence_score
        )
    )
    try:
        db.add(
            feedback_record
        )
        await db.commit()

        await db.refresh(
            feedback_record
        )
    except Exception:
        await db.rollback()
        raise
    
    return feedback_record


