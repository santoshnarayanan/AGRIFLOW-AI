"""
Field repository.

Extends BaseRepository with the one query that BaseRepository cannot provide
generically: filtering fields by their parent farm_id.

All write operations (create, update, delete) and get_by_id are inherited
from BaseRepository unchanged.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.field import Field
from app.db.repositories.base import BaseRepository


class FieldRepository(BaseRepository[Field]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Field, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> Field | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> Field:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Field | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── Field-specific queries ─────────────────────────────────────────────────

    async def get_by_farm_id(
        self,
        farm_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Field]:
        """Return all fields belonging to a farm, ordered by name."""
        result = await self._session.execute(
            select(Field)
            .where(Field.farm_id == farm_id)
            .order_by(Field.name)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
