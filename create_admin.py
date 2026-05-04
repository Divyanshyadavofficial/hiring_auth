import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.models_db.user import User as UserDB
from app.utils.security import hash_password
from sqlalchemy import select
from app.core.config import settings

async def create_admin():
    async_session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as db:
        # Check if admin already exists
        result = await db.execute(
            select(UserDB).where(UserDB.role == "admin")
        )
        admin = result.scalars().first()

        if admin:
            print(" Admin already exists")
            return

        # Create admin
        new_admin = UserDB(
            name=settings.ADMIN_NAME,
            age=settings.ADMIN_AGE,
            email=settings.ADMIN_EMAIL,
            password=hash_password(settings.ADMIN_PASSWORD),
            role="admin"
        )
        

        db.add(new_admin)
        await db.commit()

        print("✅ Admin created successfully")


if __name__ == "__main__":
    asyncio.run(create_admin())