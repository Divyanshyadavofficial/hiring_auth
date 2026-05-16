from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import ForeignKey,Integer,Text,String,Float
from app.models_db.base import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )
    attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("candidate_attempts.id")
    )
    strengths: Mapped[str] = mapped_column(Text)
    weaknesses: Mapped[str] = mapped_column(Text)
    ai_summary: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(String)