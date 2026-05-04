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