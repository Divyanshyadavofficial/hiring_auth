from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,String,ForeignKey,Text
from datetime import datetime
from sqlalchemy import DateTime,JSON,Index
from sqlalchemy.sql import func
from app.models_db import Base


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    __table_args__ = (
        Index("idx_question_assessment", "assessment_id"),
        Index("idx_question_skill", "skill_name"),
        Index("idx_question_status", "status"),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessments.id",ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(

        DateTime(timezone=True),

        server_default=func.now(),

        nullable=False

    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending_review",
        nullable=False
    )

    recruiter_feedback: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    skill_name: Mapped[str] = mapped_column(String,nullable=False)
    question_type: Mapped[str] = mapped_column(String,nullable=False)
    difficulty_level:Mapped[str] = mapped_column(String,nullable=False)
    question_text: Mapped[str] = mapped_column(Text,nullable=False)
    options: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True
    )
    expected_answer: Mapped[str] = mapped_column(Text,nullable=False)
    marks: Mapped[int] = mapped_column(Integer,nullable=False)
    time_limit_seconds: Mapped[int] = mapped_column(Integer,nullable=False)

    assessment = relationship(
        "Assessment",
        back_populates="questions"
    )

