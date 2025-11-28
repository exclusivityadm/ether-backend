# app/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ENV: str = "development"

    # Raw DATABASE_URL straight from environment
    DATABASE_URL: str

    OPENAI_API_KEY: Optional[str] = None
    CORS_ALLOW_ORIGINS: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
