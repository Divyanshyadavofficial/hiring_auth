from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import ForeignKey,Integer,Text,String,Float
from app.models_db.base import Base

class CandidateAnswer(Base):
    __tablename__ = "candidate_answers"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    attempt_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("candidate_attempts.id")
    )
    question_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_questions.id")
    )

    candidate_answer: Mapped[str] = mapped_column(Text)
    is_correct: Mapped[bool]
    obtained_marks: Mapped[float] = mapped_column(Float)
    time_taken_seconds: Mapped[int] = mapped_column(Integer)