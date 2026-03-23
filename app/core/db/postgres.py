"""
app/core/db/postgres.py

Async PostgreSQL connection pool and helper utilities.

Uses SQLAlchemy 2.x async engine with asyncpg driver.
The module exposes a lifespan-managed engine and a get_db dependency
for use in FastAPI endpoints.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import settings

# ── Engine ────────────────────────────────────────────────────────────────────

engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    echo=settings.app_env == "development",
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Dependency ────────────────────────────────────────────────────────────────

@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a SQLAlchemy AsyncSession.

    Usage in FastAPI endpoints (via Depends or direct context manager):
        async with get_db() as db:
            result = await db.execute(...)

    # TODO: Add structured error logging for unhandled DB exceptions.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Table creation helper (development only) ─────────────────────────────────

async def create_tables() -> None:
    """
    Create all mapped tables in the database.

    Call this in the application lifespan handler (development only).
    In production use Alembic migrations instead.

    # TODO: Import all ORM models so SQLAlchemy metadata is populated
    #       before calling metadata.create_all().
    """
    from sqlalchemy import text

    async with engine.begin() as conn:
        # TODO: Replace with: await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("SELECT 1"))  # smoke test
