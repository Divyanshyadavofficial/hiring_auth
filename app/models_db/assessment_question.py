from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,String,ForeignKey,Text

from app.models_db import Base

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    assessment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessments.id")
    )

    skill_name: Mapped[str] = mapped_column(String)
    question_type: Mapped[str] = mapped_column(String)
    difficulty_level:Mapped[str] = mapped_column(String)
    question_text: Mapped[str] = mapped_column(Text)
    expected_answer: Mapped[str] = mapped_column(Text)
    marks: Mapped[int] = mapped_column(Integer)
    time_limit_seconds: Mapped[int] = mapped_column(Integer)

