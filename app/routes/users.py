from fastapi import APIRouter,HTTPException,Depends
from app.models.user import User,UserResponse,UserCreate
from app.db import get_db
from app.models_db.user import User as UserDB
from app.models.user import updated_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import hash_password
from sqlalchemy import select
from app.core.config import settings

from app.utils.dependencies import require_roles,admin_or_self

user_router = APIRouter()


@user_router.post("/users")
async def create_user(user:UserCreate,db:AsyncSession=Depends(get_db)):
    new_user = UserDB(
        name = user.name,
        age = user.age,
        email = user.email,
        password=hash_password(user.password),
        role="candidate"

    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return{
        "message":"user created successfully"
    }


@user_router.get("/users/{user_id}",response_model=UserResponse)
async def get_user(
    user_id:int,
    db:AsyncSession=Depends(get_db),
    current_user = Depends(admin_or_self)

):
   user = await db.get(UserDB,user_id)
   if not user: 
       raise HTTPException(status_code=404,detail="User not found")
   if current_user:
       raise HTTPException(status_code=403,detail="invalid user")

   return user


@user_router.get("/users")
async def get_all_users(
    user = Depends(require_roles(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(UserDB))
    users = result.scalars().all()
    return users



@user_router.put("/users/{user_id}")
async def update_user(
    user_id:int,updated_user:User,
    db:AsyncSession=Depends(get_db),
    current_user = Depends(admin_or_self)


):
    if current_user:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    user = await db.get(UserDB,user_id)
    if not user:
        raise HTTPException(status_code=404,detail="User not found")
    user.name = updated_user.name
    user.age = updated_user.age
    user.email = updated_user.email

    await db.commit()
    await db.refresh(user)
    return{
        "message":"user updated successfully",
        "user":user
    }
    


@user_router.patch("/users/{user_id}")
async def update_specific_details(
    user_id:int,update_data:updated_user,
    db:AsyncSession=Depends(get_db),
    current_user = Depends(admin_or_self)
):
    if current_user:
        raise HTTPException(status_code=403, detail="Not allowed")
    
    user = await db.get(UserDB,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    update_dict = update_data.dict(exclude_unset=True)
    for key,value in update_dict.items():
        setattr(user,key,value)
    
    await db.commit()
    await db.refresh(user)
    return {
        "message": "user partially updated",
        "user": user
    }



@user_router.delete("/users/{user_id}")
async def delete_user(
    user_id:int,
    current_user=Depends(admin_or_self),                
    db:AsyncSession=Depends(get_db)
):
    if current_user:
        raise HTTPException(status_code=403, detail="Not allowed")

    user = await db.get(UserDB,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    await db.commit()
    return {"message":"user deleted successfully"}


    




