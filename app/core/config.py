from pydantic_settings import SettingsConfigDict,BaseSettings
class Settings(BaseSettings):
    DATABASE_URL:str
    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int
    ADMIN_EMAIL:str
    ADMIN_PASSWORD:str
    ADMIN_NAME:str
    ADMIN_AGE: int
    
    model_config = SettingsConfigDict(
        env_file=".env"
    )
settings = Settings()