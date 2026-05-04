from sqlalchemy.orm  import Mapped,mapped_column,relationship
from sqlalchemy import INTEGER,String,Text,ForeignKey

from app.models_db.user import Base

class Job(Base):
    __tablename__ = "jobs"
    id : Mapped[int] = mapped_column(INTEGER,primary_key=True,index=True)
    title : Mapped[str] = mapped_column(String,nullable=False)
    description : Mapped[str] = mapped_column(Text,nullable=False)

    created_by : Mapped[int] = mapped_column(INTEGER,ForeignKey("users.id"))

    recruiter = relationship("User",back_populates="jobs")
    applications = relationship("Application",back_populates="job")