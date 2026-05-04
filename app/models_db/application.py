from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,ForeignKey,String
from app.models_db.user import Base

class Application(Base):
    __tablename__ = "applications"
    id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)

    user_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))
    job_id:Mapped[int] = mapped_column(Integer,ForeignKey("jobs.id"))

    status: Mapped[str] = mapped_column(String,default="applied")

    candidate = relationship("User",back_populates="applications")
    job = relationship("Job",back_populates="applications")
    
