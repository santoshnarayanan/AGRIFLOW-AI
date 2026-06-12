"""
Crop repository.

Extends BaseRepository with crop-specific queries:

- ``list_by_field``  — paginated crop cycles for a given field, with an
                       optional status filter (pure DB predicate, not a
                       business rule).
- ``exists``         — lightweight existence probe that avoids fetching the
                       full row when only presence needs to be confirmed.

All write operations (create, update, delete) and get_by_id are inherited
from BaseRepository unchanged.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.crop import Crop, CropStatus
from app.db.repositories.base import BaseRepository


class CropRepository(BaseRepository[Crop]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Crop, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> Crop | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> Crop:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Crop | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── Crop-specific queries ──────────────────────────────────────────────────

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        status: CropStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Crop]:
        """
        Return all crop cycles belonging to a field, ordered by planting_date
        descending (most recent cycle first).

        ``status`` is an optional DB-level filter predicate.  Applying it here
        avoids fetching rows that the caller will discard, with no business
        logic coupling — the repository does not know why a particular status
        is being filtered for.
        """
        query = (
            select(Crop)
            .where(Crop.field_id == field_id)
            .order_by(Crop.planting_date.desc())
            .limit(limit)
            .offset(offset)
        )
        if status is not None:
            query = query.where(Crop.status == status)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def exists(self, record_id: uuid.UUID) -> bool:
        """
        Return True if a crop record with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.
        """
        result = await self._session.execute(
            select(Crop.id).where(Crop.id == record_id)
        )
        return result.scalar_one_or_none() is not None
