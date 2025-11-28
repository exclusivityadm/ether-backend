# app/db.py

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from sqlalchemy.engine.url import URL
from app.models.base import Base
from app.config import settings

# -----------------------------------------------------
# Database URL
# -----------------------------------------------------
RAW_DB_URL = settings.DATABASE_URL

# Force SSL and avoid IPv6 resolution issues (Render -> Supabase)
if RAW_DB_URL.startswith("postgresql"):
    # SQLAlchemy-style URL object lets us safely patch query parameters
    url_obj = URL.create(
        "postgresql+psycopg",
        username=url_obj.username if 'url_obj' in locals() else settings.DATABASE_URL.split("//")[1].split(":")[0],
        password=url_obj.password if 'url_obj' in locals() else settings.DATABASE_URL.split(":")[2].split("@")[0],
        host=url_obj.host if 'url_obj' in locals() else settings.DATABASE_URL.split("@")[1].split(":")[0],
        port=url_obj.port if 'url_obj' in locals() else 5432,
        database=url_obj.database if 'url_obj' in locals() else settings.DATABASE_URL.split("/")[-1].split("?")[0],
        query={"sslmode": "require"}
    )
    DATABASE_URL = str(url_obj)
else:
    DATABASE_URL = RAW_DB_URL

# -----------------------------------------------------
# Engine Configuration
# -----------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,          # Detect dead connections
    pool_recycle=1800,           # Reconnect every 30 minutes
    connect_args={
        "sslmode": "require",
        # Avoid IPv6 resolution issues on Render
        "options": "-c enable_ipv6=off"
    },
)

# Session local
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# -----------------------------------------------------
# Dependency: DB Session for FastAPI
# -----------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------
# Database Initialization
# -----------------------------------------------------
def init_db():
    """
    Load all models and ensure tables exist.
    """
    import app.models  # Ensures SQLAlchemy registers all models
    Base.metadata.create_all(bind=engine)
