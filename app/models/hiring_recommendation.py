from pydantic import BaseModel,ConfigDict
from typing import List

class AIHiringRecommendationResponse(BaseModel):
    recommendation: str
    confidence: float
    summary: str
    reasoning: List[str]
    strengths: list[str]
    risks: list[str]
    model_config = ConfigDict(from_attributes=True)

