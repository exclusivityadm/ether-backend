# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

from app.models.base import Base
from app.config import settings


# -----------------------------------------------------
# Engine & Session
# -----------------------------------------------------
DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# -----------------------------------------------------
# Dependency: yield database session
# -----------------------------------------------------
def get_db():
    """
    FastAPI dependency. Creates a DB session and yields it.
    Ensures proper close after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------
# Initialize DB schema
# -----------------------------------------------------
def init_db():
    """
    Initializes the database by creating all tables.
    Must import models so SQLAlchemy registers them.
    """
    import app.models  # Ensures all model classes are loaded
    Base.metadata.create_all(bind=engine)
