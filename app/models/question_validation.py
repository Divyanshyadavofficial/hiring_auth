from pydantic import BaseModel,Field
from typing import Optional,Literal

class QuestionSchema(BaseModel):
    question_type: Literal[
        "mcq",
        "coding",
        "debugging"
    ]

    difficulty_level: Literal[
        "easy",
        "medium",
        "hard"
    ]
    question_type: str
    difficulty_level: str
    question_text: str
    options: Optional[dict] = None
    correct_answer: str
    marks: int = Field(gt=0)
    time_limit_seconds: int = Field(gt=0)