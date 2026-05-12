from pydantic import BaseModel,EmailStr

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
    created_by: int

class ApplyJobResponse(BaseModel):
    message: str

class JobApplicationResponse(BaseModel):
    application_id: int
    status: str
    candidate_name: str
    candidate_email: EmailStr