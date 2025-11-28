import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Keepalive environment variables
    SUPABASE_KEEPALIVE_URLS: str = os.getenv("SUPABASE_KEEPALIVE_URLS", "")
    RENDER_KEEPALIVE_URLS: str = os.getenv("RENDER_KEEPALIVE_URLS", "")

    class Config:
        extra = "allow"


settings = Settings()
