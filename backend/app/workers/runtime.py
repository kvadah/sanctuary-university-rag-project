"""Sync <-> async bridge for the Celery worker.

The whole ingestion pipeline is async (async SQLAlchemy, ``AsyncQdrantClient``,
async ``AsyncOpenAI``), but a Celery worker is a synchronous process. We keep one
persistent asyncio event loop per worker process and drive every coroutine through
it with :func:`run_async`, so cached async clients stay bound to a single, stable
loop across tasks.

DB access uses a worker-local engine with ``NullPool``: no connection is reused
across tasks, which avoids handing an asyncpg connection created on one task to
another and keeps things safe under Celery's prefork model (one loop per child).
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Awaitable, TypeVar

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings

T = TypeVar("T")

_loop: asyncio.AbstractEventLoop | None = None
_engine = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _get_loop() -> asyncio.AbstractEventLoop:
    """Return this process's persistent event loop, creating it on first use."""
    global _loop
    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
    return _loop


def run_async(coro: Awaitable[T]) -> T:
    """Run a coroutine to completion on the persistent worker loop."""
    return _get_loop().run_until_complete(coro)


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _engine, _sessionmaker
    if _sessionmaker is None:
        _engine = create_async_engine(
            settings.SQLALCHEMY_DATABASE_URI,
            echo=settings.DEBUG,
            future=True,
            poolclass=NullPool,
        )
        _sessionmaker = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _sessionmaker


@asynccontextmanager
async def worker_session():
    """Async session scope for worker code (commit on success, rollback on error).

    Mirrors ``app.core.db.get_db`` but for the worker's engine. Each ``async with``
    is an independent unit of work, so status updates are committed even if a later
    stage fails.
    """
    async with _get_sessionmaker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
