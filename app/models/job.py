from pydantic import BaseModel,EmailStr
from typing import Literal

class JobCreate(BaseModel):
    title: str
    description: str

class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    class Config: 
        from_attributes = True

class JobCreateResponse(BaseModel):
    message: str
    job_id: int
    skills:list[str]

class ApplyJobResponse(BaseModel):
    message: str
    match_score: float

class JobApplicationResponse(BaseModel):
    application_id: int
    status: str
    candidate_name: str
    candidate_email: EmailStr
    match_score: float
    resume_url: str | None
    shortlist_status: str
    recruiter_notes: str | None = None


class SkillReview(BaseModel):
    id: int | None = None
    skill_name: str
    skill_status: Literal[
        "pending",
        "approved",
        "rejected"
    ]


class SkillReviewRequest(BaseModel):
    skills: list[SkillReview]

from pydantic import BaseModel

class JobDashboardResponse(BaseModel):
    job_id: int
    job_title: str

    total_applications: int
    assessment_completed: int

    passed_candidates: int
    failed_candidates: int

    shortlisted_candidates: int
    interview_candidates: int
    hired_candidates: int

    average_score: float