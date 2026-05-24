from pydantic import BaseModel

class QuestionReviewRequest(BaseModel):
    status: str
    recruiter_feedback: str| None = None
    question_text: str | None = None
    difficulty_level: str | None = None
    marks: int|None = None
    time_limit_seconds: int|None = None
    expected_answer: str| None = None
    options: dict | None = None