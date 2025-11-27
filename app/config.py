from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    ENV: str = "development"

    DATABASE_URL: str = "postgresql+psycopg://user:password@localhost:5432/ether"

    OPENAI_API_KEY: Optional[str] = None
    CORS_ALLOW_ORIGINS: str = ""

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
