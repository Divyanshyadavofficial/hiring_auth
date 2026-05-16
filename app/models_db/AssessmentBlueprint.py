from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,String,ForeignKey

from app.models_db import Base

class AssessmentBlueprint(Base):
    __tablename__ = "assessment_blueprints"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    
    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id")
    )
    total_questions: Mapped[int] = mapped_column(
        Integer,
        default=10
    )
    total_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=30
    )
    mcq_count: Mapped[int] = mapped_column(Integer, default=5)
    coding_count: Mapped[int] = mapped_column(Integer, default=2)
    debugging_count: Mapped[int] = mapped_column(Integer, default=1)

    difficulty_level: Mapped[str] = mapped_column(
        String,
        default="medium"
    )

    status: Mapped[str] = mapped_column(
        String,
        default="draft"
    )

class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    job_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("jobs.id")
    )

    blueprint_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_blueprints.id")
    )

    version: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending_review"
    )

    approved_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )