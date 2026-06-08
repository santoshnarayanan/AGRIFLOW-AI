"""
Farm repository.

Provides standard CRUD operations for the Farm entity via BaseRepository.
Farm-specific queries (e.g. search by farm_code) should be added here as the
domain grows; the current surface is intentionally minimal.
"""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.farm import Farm
from app.db.repositories.base import BaseRepository


class FarmRepository(BaseRepository[Farm]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Farm, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> Farm | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> Farm:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> Farm | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)
