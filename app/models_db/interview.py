from datetime import datetime

from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    DateTime,
    Float,
    Text
)

from app.models_db.base import Base

class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id")
    )

    interviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )

    round_number: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime
    )

    meeting_link: Mapped[str|None] = mapped_column(
        String,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String,
        default="scheduled"
    )
    started_at: Mapped[datetime|None] = mapped_column(
          DateTime(timezone=True),
          nullable=True
    )
    completed_at: Mapped[datetime|None] = mapped_column(
          DateTime(timezone=True),
          nullable=True
    )

class InterviewFeedback(Base):
        __tablename__ = "interview_feedback"
        id: Mapped[int] = mapped_column(
            Integer,
            primary_key=True
        )

        interview_id: Mapped[int] = mapped_column(
            Integer,
            ForeignKey(
                "interviews.id",
                ondelete="CASCADE"
            ),
            unique=True
        )

        technical_score: Mapped[float] = mapped_column(Float)
        communication_score: Mapped[float] = mapped_column(Float)
        problem_solving_score: Mapped[float] = mapped_column(Float)
        strengths: Mapped[str] = mapped_column(Text)
        
        weaknesses: Mapped[str] = mapped_column(Text)
        recommendation: Mapped[str] = mapped_column(Text)
        overall_score: Mapped[float] = mapped_column(Float)


    
