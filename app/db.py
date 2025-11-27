# app/db.py

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.settings import settings

# ----------------------------------------------------------
# Engine & Session
# ----------------------------------------------------------

DATABASE_URL: str = settings.DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency: yields a SQLAlchemy session and
    always closes it after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Non-FastAPI helper context manager, useful for internal
    jobs (cron, keepalive tasks that need DB, etc.).
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Optional helper to create tables based on models.
    Not called automatically; you can import and run
    this manually when you're ready to create schema.
    """
    # Import models so Base.metadata has all tables
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
