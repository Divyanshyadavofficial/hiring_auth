from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer, String,Float,ForeignKey

from app.models_db.base import Base

class JobSkill(Base):
    __tablename__ ="job_skills"
    id: Mapped[int] = mapped_column(Integer,primary_key=True)

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id")
    )

    skill_name: Mapped[str] = mapped_column(
        String,
        index=True
    )

    skill_status: Mapped[str] = mapped_column(
    String,
    default="pending"
    )

    importance_weight: Mapped[float] = mapped_column(
        Float,
        default=1.0
    )
    difficulty_level: Mapped[str] = mapped_column(
        String,
        default="medium"
    )
