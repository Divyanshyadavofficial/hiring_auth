from sqlalchemy.orm import Mapped,mapped_column
from sqlalchemy import (
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime
)

from datetime import datetime

from app.models_db.base import Base

class Notifications(Base):
    __tablename__="notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id")
    )

    title: Mapped[str] = mapped_column(
        String
    )

    message: Mapped[str] = mapped_column(
        String
    )

    type: Mapped[str] = mapped_column(
        String
    )

    is_read: Mapped[bool] = mapped_column(Boolean,default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )