from pydantic import BaseModel


class AssessmentFeedbackSchema(BaseModel):
    strengths: list[str]
    weaknesses: list[str]
    recommendation: str
    overall_summary: str
    confidence_score: float