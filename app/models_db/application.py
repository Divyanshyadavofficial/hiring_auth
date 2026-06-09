from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,ForeignKey,String,UniqueConstraint
from app.models_db.base import Base
from sqlalchemy import Index,Integer,ForeignKey,String,Float,Text

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint('user_id','job_id',name='unique_user_job'),
        Index("idx_application_user","user_id"),
        Index("idx_application_job","job_id"),
        Index("idx_application_status","status"),
    )
    id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)
    user_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))
    job_id:Mapped[int] = mapped_column(Integer,ForeignKey("jobs.id"))
    status: Mapped[str] = mapped_column(String,default="pending")
    match_score:Mapped[float] = mapped_column(Float,nullable=True)
    shortlist_status: Mapped[str] = mapped_column(
    String,
    default="pending"
    )
    recruiter_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True

    )

    candidate = relationship("User",back_populates="applications")
    job = relationship("Job",back_populates="applications")

