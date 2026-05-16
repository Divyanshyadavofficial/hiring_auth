from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import ForeignKey,Integer,Text,String,Float
from app.models_db.base import Base

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

    started_at = mapped_column(nullable=True)

    completed_at = mapped_column(nullable=True)

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