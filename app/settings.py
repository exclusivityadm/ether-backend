# app/settings.py

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ----------------------------------------------------------
    # Core service
    # ----------------------------------------------------------
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # ----------------------------------------------------------
    # Supabase
    # ----------------------------------------------------------
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None

    # ----------------------------------------------------------
    # Database URL (Postgres / Supabase)
    # ----------------------------------------------------------
    DATABASE_URL: str

    # ----------------------------------------------------------
    # OpenAI
    # ----------------------------------------------------------
    OPENAI_API_KEY: str

    # ----------------------------------------------------------
    # Keepalive URLs (comma-separated lists)
    # ----------------------------------------------------------
    SUPABASE_KEEPALIVE_URLS: Optional[str] = None
    RENDER_KEEPALIVE_URLS: Optional[str] = None
    VERCEL_KEEPALIVE_URLS: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
