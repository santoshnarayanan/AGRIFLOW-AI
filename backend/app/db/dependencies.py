"""
FastAPI dependency that provides a scoped AsyncSession per request.

Usage in a router:

    from app.db.dependencies import get_db
    from sqlalchemy.ext.asyncio import AsyncSession

    @router.get("/example")
    async def my_endpoint(db: AsyncSession = Depends(get_db)):
        ...
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionFactory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional database session; rollback on exception."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
