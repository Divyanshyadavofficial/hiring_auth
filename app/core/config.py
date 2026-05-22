from pydantic_settings import SettingsConfigDict,BaseSettings
from functools import lru_cache
class Settings(BaseSettings):
    DATABASE_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    ADMIN_EMAIL:str
    ADMIN_PASSWORD:str
    ADMIN_NAME:str
    ADMIN_AGE: int
    CHROMA_DB_PATH:str
    EMBEDDING_MODEL:str
    GROQ_API_KEY:str
    GROQ_MODEL:str
    
    model_config = SettingsConfigDict(
        env_file=".env"
    )
@lru_cache(maxsize=1)
def get_settings():
    return Settings()