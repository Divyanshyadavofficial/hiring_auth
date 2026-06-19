from pydantic import BaseModel
from datetime import date,datetime

class OfferCreateRequest(BaseModel):
    salary: float
    joining_date: date
    offer_letter_url: str | None = None

class OfferResponse(BaseModel):
    id: int
    application_id: int
    salary: float
    joining_date: date
    offer_letter_url: str | None
    status: str
    created_at: datetime | None
    accepted_at: datetime | None
    declined_at: datetime | None
    class Config:
        from_attributes = True