from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey,Integer,Text,String,Float,Boolean
from app.models_db.base import Base
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy.sql import func


class CandidateAttempt(Base):
    __tablename__ = "candidate_attempts"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id")
    )
    assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessments.id")
    )

    started_at:Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.mow()
    )

    completed_at: Mapped[datetime|None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    total_score: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )
    
    percentage: Mapped[float] = mapped_column(
        Float,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String,
        default="in_progress"
    )
    passed: Mapped[bool] = mapped_column(

        Boolean,

        default=False,

        nullable=False

    )

    answers = relationship(
        "CandidateAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan"

    )