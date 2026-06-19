from sqlalchemy.orm import Mapped,mapped_column

from sqlalchemy import (
    Integer,
    Float,
    String,
    Date,
    ForeignKey,
    DateTime
)
from datetime import datetime
from app.models_db.base import Base

class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("application.id"),
        unique=True
    )

    salary: Mapped[float] = mapped_column(
        Float
    )

    joining_date: Mapped[str] = mapped_column(Date)

    offer_letter_url: Mapped[str|None] = mapped_column(
        String,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String,
        default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    accepted_at: Mapped[datetime |None] = mapped_column(
        DateTime,
        nullable=True
    )

    declined_at: Mapped[datetime|None] = mapped_column(
        DateTime,
        nullable=True
    )