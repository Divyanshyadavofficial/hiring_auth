from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import Integer,ForeignKey,Text,Float,JSON

from app.models_db.base import Base

class AssessmentFeedback(Base):
    __tablename__ = "assessment_feedback"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "candidate_attempts.id",
            ondelete="CASCADE"
        ),
        unique=True
    )

    strengths: Mapped[list] = mapped_column(
        JSON
    )

    weaknesses: Mapped[list] = mapped_column(
        JSON
    )

    recommendation: Mapped[str] = mapped_column(
        Text
    )

    overall_summary: Mapped[str] = mapped_column(
        Text
    )

    confidence_score: Mapped[float] = mapped_column(
        Float
    )