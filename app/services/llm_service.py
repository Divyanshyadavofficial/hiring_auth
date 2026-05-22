import os
from langchain_groq import ChatGroq

from dotenv import load_dotenv
from app.core.config import get_settings

load_dotenv()
settings = get_settings()
llm = ChatGroq(
    groq_api_key = settings.GROQ_API_KEY,
    model_name=settings.GROQ_MODEL,
    temperature=0.3
)

