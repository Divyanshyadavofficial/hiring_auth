from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import ForeignKey,Integer,Text,String
from app.models_db.base import Base


class RecruiterReview(Base):
    __tablename__ = "recruiter_reviews"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessments.id")
    )

    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_questions.id")
    )

    reviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )

    action: Mapped[str] = mapped_column(String)
    feedback: Mapped[str] = mapped_column(Text)