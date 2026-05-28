from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import ForeignKey,Integer,Text,String,Float,Boolean,UniqueConstraint
from app.models_db.base import Base
class CandidateAnswer(Base):
    __tablename__ = "candidate_answers"

    __table_args__ = (
        UniqueConstraint(
            "attempt_id",
            "question_id",
            name="unique_attempt_question"
        ),
    )
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    attempt_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("candidate_attempts.id",ondelete="CASCADE"),
        nullable=False
    )
    question_id:Mapped[int] = mapped_column(
        Integer,
        ForeignKey("assessment_questions.id",
                ondelete="CASCADE"
        ),
        nullable=False
    )

    candidate_answer: Mapped[str|None] = mapped_column(Text,nullable=True)
    is_correct: Mapped[bool] = mapped_column(Boolean,nullable=False,default=False)
    obtained_marks: Mapped[float] = mapped_column(Float,default=0)
    time_taken_seconds: Mapped[int|None] = mapped_column(Integer,nullable=True)
    status: Mapped[str] = mapped_column(
        String,
        default="unanswered"
    )

    attempt = relationship(
        "CandidateAttempt",
        back_populates="answers"
    )