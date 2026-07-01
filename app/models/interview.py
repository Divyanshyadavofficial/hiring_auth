from datetime import datetime
from pydantic import BaseModel

from typing import Literal


class InterviewDashboardResponse(BaseModel):
    interview_id: int
    application_id: int
    candidate_id: int
    candidate_name: str
    candidate_email: str
    job_id: int
    job_title: str
    round_number: int
    scheduled_at: datetime
    meeting_link: str | None
    status: str

class InterviewCreateRequest(BaseModel):
    interviewer_id : int
    round_number: int =1
    scheduled_at: datetime
    meeting_link: str|None = None

class InterviewResposnse(BaseModel):
    id: int
    application_id: int
    round_number: int
    scheduled_at: datetime
    meeting_link: str|None
    status: str

    class Config:
        from_attributes = True

class InterviewFeedbackRequest(BaseModel):
    technical_score: float
    communication_score: float
    problem_solving_score: float
    strengths: str
    weaknesses: str
    recommendation: str

    recommendation: Literal[
        "strong_hire",
        "hire",
        "hold",
        "reject"
    ]