from fastapi import FastAPI
from app.routes.users import user_router
from app.models_db.models_db import User as UserDB
from app.models.models import User
from app.models_db.models_db import Base
from app.db import engine
from app.routes.auth import auth_router
from app.routes.admin import admin_router
from app.routes.jobs import jobs_router

app = FastAPI(docs_url=None,redoc_url=None)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        
        await conn.run_sync(Base.metadata.create_all)
@app.get("/")
def root():
    return{"message":"Api Running"}

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(jobs_router)