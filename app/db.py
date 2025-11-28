from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker
from app.settings import settings
from app.models import Base


# ---------------------------------------------------------
# DATABASE ENGINE (ASYNC POSTGRES)
# ---------------------------------------------------------
DATABASE_URL = settings.DATABASE_URL

# Supabase requires asyncpg with SQLAlchemy 2.x
engine = create_async_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


# ---------------------------------------------------------
# Dependency: yield async session
# ---------------------------------------------------------
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------
# Create database schema on startup
# Safe — only creates missing tables
# ---------------------------------------------------------
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
