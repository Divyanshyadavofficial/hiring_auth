from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from sqlalchemy import String
from app.models_db.base import Base




class User(Base):
    __tablename__ ="users"
    id: Mapped[int] = mapped_column(nullable=False,index=True,primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False,unique=True)
    password: Mapped[str] = mapped_column(nullable=False)
    role:Mapped[str] = mapped_column(String,default="candidate")
    resume_url:Mapped[str] = mapped_column(String,nullable=True)

    jobs = relationship("Job",back_populates="recruiter")
    applications = relationship("Application",back_populates="candidate")
    

    
class BlacklistToken(Base):
    __tablename__ = "blacklist_tokens"

    jti: Mapped[str] = mapped_column(String,primary_key=True)

