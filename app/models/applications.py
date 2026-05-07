from pydantic import BaseModel

class ApplyRequest(BaseModel):
    job_id: int

class ApplicationResponse(BaseModel):
    id: int
    user_id: int
    jobs_id: int
    status: str
    class Config: 
        from_attributes = True

class ApplicationStatusUpdate(BaseModel):
    status: str

class CandidateDashboardResponse(BaseModel):
    total: int
    pending: int
    accepted: int
    rejected: int

class RecruiterApplicationResponse(BaseModel):
    application_id: int
    status: str
    candidate_name: str
    candidate_email: str