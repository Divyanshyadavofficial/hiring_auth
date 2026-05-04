from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPBearer
from app.utils.jwt import verify_token
from app.db import get_db
from app.models_db.user import User as UserDB

security = HTTPBearer()

async def get_current_user(
        credentials = Depends(security),
        db = Depends(get_db)
):
    token = credentials.credentials 
    payload =  await verify_token(token,db)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user = await db.get(UserDB,payload["user_id"])
    return {
        "user_id":user.id,
        "role":user.role
    }


def require_roles(allowed_roles:list):
    async def role_checker(current_user = Depends(get_current_user)):

        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker

def admin_or_self(user_id: int):
    async def checker(current_user=Depends(get_current_user)):
        if current_user["role"] != "admin" and current_user["user_id"] != user_id:
            raise HTTPException(status_code=403)
        return current_user
    return checker