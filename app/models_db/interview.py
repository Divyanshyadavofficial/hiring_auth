from datetime import datetime

from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import (
    Integer,
    ForeignKey,
    String,
    DateTime
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