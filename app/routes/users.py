from fastapi import APIRouter,HTTPException,Depends,UploadFile,File
import os
import shutil
from app.models.user import User,UserResponse,UserCreate
from app.db import get_db
from app.models_db.user import User as UserDB
from app.models.user import updated_user
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.security import hash_password
from sqlalchemy import select,delete
from app.core.config import get_settings
settings = get_settings()

from app.models_db.resume_skill import ResumeSkill

from app.utils.dependencies import require_roles,admin_or_self

from app.services.resume_service import extract_text_from_pdf
from app.services.skill_extractor import extract_skills
from app.services.embedding_service import generate_embedding
from app.vector_db.chroma_client import get_resume_collection


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



# Upload Resume
# → save file
# → enqueue task
# → background worker generates embeddings
# → save to vector DB
#   
@user_router.post("/upload-resume")
async def upload_resume(
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
    current_user = Depends(require_roles(["candidate"]))
):
    if file.content_type !="application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files allowed"
        )
    upload_dir = "uploads/resumes"

    os.makedirs(upload_dir,exist_ok=True)

    file_path = f"{upload_dir}/{current_user['user_id']}_{file.filename}"

    with open(file_path,"wb") as buffer:
        shutil.copyfileobj(file.file,buffer)
    user = await db.get(UserDB,current_user["user_id"])
    user.resume_url = file_path
    text = extract_text_from_pdf(file_path)
    skills = extract_skills(text)
    embedding = generate_embedding(text)

    resume_collection = (
        get_resume_collection()
    )
    resume_collection.upsert(
        ids=[str(current_user["user_id"])],
        embeddings=[embedding],
        documents=[text],
        metadatas=[
            {
                "user_id": current_user["user_id"]
            }
        ]
    )
    
    await db.execute(
        delete(ResumeSkill).where(
            ResumeSkill.user_id == current_user["user_id"]
        )
    )
    for skill in skills:
        db_skill = ResumeSkill(
            user_id=current_user["user_id"],
            skill_name = skill
        )
        db.add(db_skill)
    await db.commit()
    return{
        "message":"Resume uploaded successfully",
        "resume_url":file_path,
        "skills":skills
    }

