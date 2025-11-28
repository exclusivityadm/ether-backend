# app/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine.url import make_url
from app.models.base import Base
from app.config import settings
import logging

log = logging.getLogger("uvicorn")

# -----------------------------------------------------
# Normalize DATABASE_URL
# -----------------------------------------------------
raw_url = settings.DATABASE_URL

# Parse with SQLAlchemy (safe, structured)
url = make_url(raw_url)

# Force dialect to psycopg
url = url.set(
    drivername="postgresql+psycopg",
)

# Always enforce SSL and IPv4
url = url.update_query_dict({
    "sslmode": "require",
})


DATABASE_URL = str(url)
log.info(f"Using normalized DATABASE_URL: {DATABASE_URL}")

# -----------------------------------------------------
# Engine
# -----------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={
        "sslmode": "require",
        # Force IPv4-only resolution (Render → Supabase fix)
        "target_session_attrs": "read-write",
        "options": "-c inet_server_addr=0.0.0.0"
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

# -----------------------------------------------------
# Dependency
# -----------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------------------------------
# Initialize
# -----------------------------------------------------
async def init_db():
    """
    Creates tables on startup.
    """
    import app.models
    log.info("Initializing database schema…")
    Base.metadata.create_all(bind=engine)
    log.info("Database ready.")
