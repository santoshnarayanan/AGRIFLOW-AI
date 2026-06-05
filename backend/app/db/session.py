"""
Async SQLAlchemy engine and session factory.

Uses asyncpg driver for non-blocking PostgreSQL access — critical for FastAPI's
async request handlers.  Connection pool is tuned for a single-container baseline
and can be overridden via env vars for high-throughput deployments.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_settings = get_settings()


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        str(_settings.DATABASE_URL),
        echo=_settings.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,   # recycle stale connections automatically
        pool_recycle=1800,    # recycle every 30 min to avoid idle-timeout drops
    )


engine: AsyncEngine = _build_engine()

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # objects remain usable after commit in async context
    autoflush=False,
    autocommit=False,
)
