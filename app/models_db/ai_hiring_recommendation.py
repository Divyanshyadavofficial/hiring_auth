from datetime import datetime
from sqlalchemy.orm import relationship

from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    Float,
    DateTime,
    JSON,
    UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models_db.base import Base


class AIHiringRecommendation(Base):
    __tablename__ = "ai_hiring_recommendations"

    __table_args__ = (
        UniqueConstraint(
            "application_id",
            name="uq_ai_recommendation_application"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id")
    )

    recommendation: Mapped[str] = mapped_column(
        String
    )

    confidence: Mapped[float] = mapped_column(
        Float
    )

    summary: Mapped[str] = mapped_column(
        String
    )

    reasoning: Mapped[list] = mapped_column(
        JSON
    )

    strengths: Mapped[list] = mapped_column(
        JSON
    )

    risks: Mapped[list] = mapped_column(
        JSON
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
    application = relationship(
        "Application",
        back_populates="ai_recommendation"
    )