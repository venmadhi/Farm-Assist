import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgriGenie AI"
    API_V1_STR: str = "/api/v1"
    
    # Database connection URL. Defaults to local SQLite for instant setup.
    DATABASE_URL: str = "sqlite:///./agrigenie.db"
    
    # JWT Auth configurations
    SECRET_KEY: str = "SUPER_SECRET_AGRIGENIE_KEY_FOR_KERALA_FARMERS_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days token expiration
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
