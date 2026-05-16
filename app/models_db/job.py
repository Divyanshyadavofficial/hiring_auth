from sqlalchemy.orm  import Mapped,mapped_column,relationship
from sqlalchemy import INTEGER,String,Text,ForeignKey,Index

from app.models_db.base import Base

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        Index("idx_job_title","title"),
        Index("idx_job_creator", "created_by"),

    )
    id : Mapped[int] = mapped_column(INTEGER,primary_key=True,index=True)
    title : Mapped[str] = mapped_column(String,nullable=False)
    description : Mapped[str] = mapped_column(Text,nullable=False)

    created_by : Mapped[int] = mapped_column(INTEGER,ForeignKey("users.id"))

    recruiter = relationship("User",back_populates="jobs")
    applications = relationship("Application",back_populates="job")
    skills = relationship(
        "JobSkill",
        backref="job",
        cascade="all,delete-orphan"
    )