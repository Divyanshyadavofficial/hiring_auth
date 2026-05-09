from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import Integer,String,ForeignKey
from app.models_db.user import Base

class ResumeSkill(Base):
    __tablename__ = "resume_skills"
    id: Mapped[int] = mapped_column(Integer,primary_key=True)

    user_id:Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))

    skill_name:Mapped[str] = mapped_column(String,index=True)

