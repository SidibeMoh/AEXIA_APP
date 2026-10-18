from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://ibi_user:IbiPassword2026!@ibi_db:5432/IBI_DataBase"
    SECRET_KEY: str = "changeme_secret_key_at_least_32_chars_long_please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    API_TITLE: str = "AEXIA Platform API"
    API_VERSION: str = "1.0.0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()