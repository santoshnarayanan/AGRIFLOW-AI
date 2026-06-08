"""
Shared FastAPI dependency providers.

Every route that needs a database session or a domain service receives it
through one of the ``Annotated`` aliases defined here.  This keeps route
signatures lean and ensures a single transaction per request.

Session lifecycle
-----------------
``get_session`` opens an ``AsyncSession``, begins an explicit transaction, and
yields to the route handler.  On success the transaction is committed; on any
unhandled exception it is rolled back.  The session is closed in all cases
because ``AsyncSessionFactory`` is used as an async context manager.
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.farm import FarmRepository
from app.db.repositories.field import FieldRepository
from app.db.session import AsyncSessionFactory
from app.services.field import FieldService


# ── Database session ──────────────────────────────────────────────────────────


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession for the duration of one request."""
    async with AsyncSessionFactory() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ── Domain service factories ──────────────────────────────────────────────────


def get_field_service(session: SessionDep) -> FieldService:
    """Construct a ``FieldService`` wired to the request-scoped session."""
    return FieldService(
        field_repository=FieldRepository(session),
        farm_repository=FarmRepository(session),
    )


FieldServiceDep = Annotated[FieldService, Depends(get_field_service)]
