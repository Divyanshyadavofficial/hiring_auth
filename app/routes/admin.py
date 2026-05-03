from fastapi import APIRouter,Depends,HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.utils.dependencies import require_roles
from app.models_db.models_db import User as UserDB




admin_router = APIRouter()



@admin_router.get("/admin")
async def admin_route(
    user = Depends(require_roles(["admin"]))
):
    return {"message":"Welcome Admin"}

@admin_router.patch("/users/{user_id}/make-admin")
async def make_admin(
    user_id: int,
    role: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(require_roles(["admin"]))
):
    user = await db.get(UserDB,user_id)
    if not user:
        raise HTTPException(status_code=404)
    user.role = "admin"
    await db.commit()
    return {f"message":"User promoted to admin"}

