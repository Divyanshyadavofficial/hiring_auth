from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import Integer,ForeignKey,String,Text

from app.models_db.base import Base

class CandidateShortlist(Base):
    __tablename__ = "candidate_shortlists"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    application_id: Mapped[int] = mapped_column(
        ForeignKey("application.id"),
        unique=True
    )

    recruiter_decision: Mapped[str] = mapped_column(
        String,
        default="pending"
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )