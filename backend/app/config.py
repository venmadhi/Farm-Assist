import os
import secrets
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AgriGenie AI"
    API_V1_STR: str = "/api/v1"
    
    # Database connection URL. Defaults to local SQLite for instant setup.
    DATABASE_URL: str = "sqlite:///./agrigenie.db"
    
    # JWT Auth configurations
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("SECRET_KEY") or secrets.token_urlsafe(32))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days token expiration
    CLOUDFLARE_WORKER_CHAT_URL: str = ""
    CLOUDFLARE_WORKER_AUTH_TOKEN: str = ""
    GEMINI_API_KEY: str = ""
    
    DEBUG_DIAGNOSIS: bool = False
    
    model_config = SettingsConfigDict(
        env_file=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")),
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
