import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from urllib.parse import quote_plus

Base = declarative_base()

def build_connection_string():
    raw = os.getenv("DATABASE_URL")
    if not raw:
        raise RuntimeError("DATABASE_URL missing")

    # Remove any options already in the URL — we will override manually
    if "options=" in raw:
        raw = raw.split("options=")[0].rstrip("&?")

    return raw

DATABASE_URL = build_connection_string()

# ----------------------------------------------------------
# HARD-FORCE IPv4 by injecting psycopg connection parameters
# ----------------------------------------------------------
connect_args = {
    # critical flag that psycopg obeys even if Render rewrites the URL
    "options": "-c enable_ipv6=off"
}

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)

async def init_db():
    """
    Create tables at startup.
    """
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise
