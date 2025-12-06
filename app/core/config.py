from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --------------------------------------------------
    # Core
    # --------------------------------------------------
    ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    PROJECT_NAME: str = "Ether API"
    VERSION: str = "2.0.0"
    API_V1_PREFIX: str = "/api"

    # --------------------------------------------------
    # Database
    # --------------------------------------------------
    DATABASE_URL: str = Field(
        default="sqlite:///./dev.db",
        description="SQLAlchemy URL. For Supabase, use the full postgres:// URL.",
    )

    # --------------------------------------------------
    # OpenAI / AI
    # --------------------------------------------------
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_TEMPERATURE: float = 0.2

    # --------------------------------------------------
    # Storage
    # --------------------------------------------------
    STORAGE_BACKEND: str = Field(
        default="local", description="local | s3 | supabase"
    )
    LOCAL_STORAGE_PATH: str = "./storage"

    # Optional S3-style config (for future cloud wiring)
    S3_BUCKET: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None

    # Optional Supabase-style config (for future wiring)
    SUPABASE_URL: Optional[str] = None
    SUPABASE_KEY: Optional[str] = None
    SUPABASE_BUCKET: Optional[str] = None

    # --------------------------------------------------
    # Auth / Merchants
    # --------------------------------------------------
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_SUPER_SECRET")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h

    # Shopify placeholders for future wiring
    SHOPIFY_API_KEY: Optional[str] = None
    SHOPIFY_API_SECRET: Optional[str] = None
    SHOPIFY_WEBHOOK_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignore unknown env vars instead of crashing
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


class HealthStatus(BaseModel):
    status: str = "ok"
    version: str
    env: str
    database_connected: bool = False
    ocr_ready: bool = False
    ai_ready: bool = False
