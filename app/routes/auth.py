
from fastapi import APIRouter,Depends,HTTPException
from app.models.models import UserLogin,RefreshTokenRequest

from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.utils.dependencies import get_current_user
from app.models_db.models_db import User as UserDB,BlacklistToken
from sqlalchemy import select
from app.utils.jwt  import create_access_token,create_refresh_token,verify_token
from app.utils.security import verify_password


auth_router = APIRouter()


@auth_router.post("/login")
async def login(user:UserLogin,db:AsyncSession=Depends(get_db)):
    result = await db.execute(
        select(UserDB).where(UserDB.email == user.email)

    )
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=400,detail="Invalid credentials")
    if not verify_password(user.password,db_user.password):
        raise HTTPException(status_code=400,detail="Invalid credentials")
    access_token = create_access_token({
        "user_id":db_user.id,
        "email":db_user.email,
        "role":db_user.role
    })
    refresh_token = create_refresh_token({"user_id":db_user.id,"email":db_user.email})

    return {
        "access_token":access_token,
        "refresh_token":refresh_token
    }



@auth_router.post("/refresh")
async def refresh_token(data:RefreshTokenRequest):
    payload = verify_token(data.refresh_token)
    if payload["type"] != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    if payload is None:
        raise HTTPException(status_code=401,detail="Invalid refresh token")
    result = await UserDB.execute(
    select(UserDB).where(UserDB.id == payload["user_id"])
    )
    user = result.scalar_one()

    new_access_token = create_access_token({
    "user_id": user.id,
    "role": user.role
    })
    
    return {"access_token":new_access_token}


@auth_router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    
    jti = current_user.get("jti")
    token_entry = BlacklistToken(jti=jti)

    db.add(token_entry)
    await db.commit()
    return {"message":"Logged out successfully"}