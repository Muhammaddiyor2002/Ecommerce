"""Async SQLAlchemy engine + session factory.

We share the same Postgres database with Django but use SQLAlchemy core for
read-mostly endpoints. This keeps the FastAPI service free of Django ORM
overhead while still pointing at the canonical schema.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .config import get_settings

_settings = get_settings()


_engine_kwargs: dict = {
    "pool_pre_ping": True,
    "pool_recycle": 1800,
    "echo": _settings.debug and _settings.env == "dev",
}
# SQLite (used in tests) uses NullPool — pool_size/max_overflow are invalid there.
if not _settings.async_database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = _settings.db_pool_size
    _engine_kwargs["max_overflow"] = _settings.db_max_overflow

engine = create_async_engine(_settings.async_database_url, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
