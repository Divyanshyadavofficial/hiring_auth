from app.models_db.AssessmentBlueprint import AssessmentBlueprint,Assessment
from app.models_db.assessment_question import AssessmentQuestion
from app.models_db.job_skill import  JobSkill
from fastapi import Depends
from app.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.services.llm_service import llm
import json
from app.models.question_validation import QuestionSchema

def build_question_prompt(skill_name,
                        question_count,
                        difficulty_distribution
):
    return f"""
        Generate {question_count} assessment questions for {skill_name}.

        Difficulty distribution:
        {difficulty_distribution}
        Return valid JSON only.

        Format:
        [
            {{
                "question_type": "mcq",

                "difficulty_level": "easy",

                "question_text": "What is Python?",

                "options": {{
                    "A": "Programming Language",

                    "B": "Database",

                    "C": "Framework",

                    "D": "Cloud Service"

                }},
                "correct_answer": "A",
                "marks": 5,
                "time_limit_seconds": 60
            }}
        ]    
    """


async def generate_questions_for_assessment(
    assessment_id: int,
    db: AsyncSession
):
    try:
        assessment = await db.get(
            Assessment,
            assessment_id
        )
        if not assessment:
            raise Exception(
                "Assessment not found"
            )

        blueprint = await db.get(
            AssessmentBlueprint,
            assessment.blueprint_id
        )

        if not blueprint:
            raise Exception(
                "Blueprint not found"
            )

        existing_questions_result = await db.execute(
            select(AssessmentQuestion).where(
                AssessmentQuestion.assessment_id == assessment.id
            )
        )

        existing_question = (
            existing_questions_result
            .scalars()
            .first()
        )

        if existing_question:
            raise Exception(
                "Questions already generated for this assessment"
            )

        

        result = await db.execute(
            select(JobSkill).where(
                JobSkill.job_id == assessment.job_id,
                JobSkill.skill_status == "approved"
            )
        )
        skills = result.scalars().all()
        if not skills:
            raise Exception(
                "No approved skills found"
            )

        total_generated_questions = 0
        for skill in skills:
            skill_name = skill.skill_name
            question_count = (
                blueprint.skill_distribution.get(
                    skill_name,
                    0
                )
            )
            if question_count == 0:
                continue

            prompt = build_question_prompt(
                skill_name=skill_name,
                question_count=question_count,
                difficulty_distribution=(
                    blueprint.difficulty_distribution
                )

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

            try:
                questions = json.loads(content)
            except json.JSONDecodeError:
                print(
                    f"Invalid JSON returned "
                    f"for skill: {skill_name}"
                )

                continue
            if not questions:
                print(
                    f"No questions generated "
                    f"for skill: {skill_name}"
                )
                continue

            validated_questions = []
            for question in questions:
                try:
                    validated_question = (
                        QuestionSchema(
                            **question
                        )
                    )
                    validated_questions.append(
                        validated_question
                    )
                except Exception as e:
                    print(
                        f"Validation failed "
                        f"for {skill_name}: {e}"
                    )
            if (
                len(validated_questions)
                != question_count
            ):
                print(
                    f"Expected "
                    f"{question_count} questions "
                    f"but got "
                    f"{len(validated_questions)} "
                    f"for skill {skill_name}"
                )

            for question in validated_questions:
                new_question = (
                    AssessmentQuestion(
                        assessment_id=assessment.id,
                        skill_name=skill_name,
                        question_type=(
                            question.question_type
                        ),
                        difficulty_level=(
                            question.difficulty_level
                        ),
                        question_text=(
                            question.question_text
                        ),
                        options=question.options,
                        expected_answer=(
                            question.correct_answer
                        ),
                        marks=question.marks,
                        time_limit_seconds=(
                            question.time_limit_seconds
                        ),
                        status="pending_review"

                    )
                )
                db.add(new_question)
                total_generated_questions += 1
        assessment.status = "questions_generated"
        await db.commit()
        return {
            "message": "Questions generated successfully",
            "assessment_id": assessment.id,
            "total_generated_questions": (
                total_generated_questions
            )
        }
    except Exception as e:
        await db.rollback()
        raise Exception(
            f"Question generation failed: {str(e)}"
        )