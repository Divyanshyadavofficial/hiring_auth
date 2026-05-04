from sqlalchemy.orm import Mapped,mapped_column,relationship
from sqlalchemy import Integer,ForeignKey,String,UniqueConstraint
from app.models_db.user import Base

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint('user_id','job_id',name='unique_user_job')
    )
    id : Mapped[int] = mapped_column(Integer,primary_key=True,index=True)

    user_id: Mapped[int] = mapped_column(Integer,ForeignKey("users.id"))
    job_id:Mapped[int] = mapped_column(Integer,ForeignKey("jobs.id"))

    status: Mapped[str] = mapped_column(String,default="pending")

    candidate = relationship("User",back_populates="applications")
    job = relationship("Job",back_populates="applications")

