# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base     # <-- FIXED: import directly from base.py
from app.config import settings

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initializes the database by creating all tables.
    All models are already imported in app/models/__init__.py,
    which registers them with SQLAlchemy metadata.
    """
    import app.models  # Required so SQLAlchemy sees all model classes
    Base.metadata.create_all(bind=engine)
