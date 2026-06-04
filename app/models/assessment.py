from pydantic import BaseModel

class SubmitAnswerRequest(BaseModel):
    answer: str
    time_taken_seconds: int