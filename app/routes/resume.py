import os
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.models_db.user import User

from app.utils.dependencies import require_roles

resume_router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


@resume_router.get("/{user_id}")
async def download_resume(
    user_id: int,
    db: AsyncSession = Depends(get_db),

    current_user = Depends(
        require_roles(["admin","recruiter"])
    )
):
    user = await db.get(User,user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    if not user.resume_url:
        raise HTTPException(
            status_code=404,
            detail="Resume not uploaded"
        )
    if not os.path.exists(user.resume_url):
        raise HTTPException(
            status_code=404,
            detail="Resume file missing"
        )
    return FileResponse(
        path=user.resume_url,
        media_type="application/pdf",
        filename=os.path.basename(
            user.resume_url
        )
    )