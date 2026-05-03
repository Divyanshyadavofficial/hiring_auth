from fastapi import APIRouter,Depends
from app.utils.dependencies import require_roles

jobs_router = APIRouter()

@jobs_router.post("/jobs")
async def create_job(
    user = Depends(require_roles(["recruiter", "admin"]))
):
    return {"message": "Job created"}


@jobs_router.post("/apply")
async def apply_job(
    user = Depends(require_roles(["candidate"]))
):
    return {"message": "Applied"}

