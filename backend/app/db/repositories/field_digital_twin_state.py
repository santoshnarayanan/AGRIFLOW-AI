"""Persistence for field Digital Twin state documents."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.field_digital_twin_state import FieldDigitalTwinState
from app.db.repositories.base import BaseRepository


class FieldDigitalTwinStateRepository(BaseRepository[FieldDigitalTwinState]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FieldDigitalTwinState, session)

    async def get_by_field_id(self, field_id: uuid.UUID) -> FieldDigitalTwinState | None:
        result = await self._session.execute(
            select(FieldDigitalTwinState).where(FieldDigitalTwinState.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def upsert_for_field(
        self,
        field_id: uuid.UUID,
        data: dict[str, Any],
    ) -> FieldDigitalTwinState:
        existing = await self.get_by_field_id(field_id)
        if existing is None:
            return await self.create({"field_id": field_id, **data})
        updated = await self.update(existing.id, data)
        assert updated is not None
        return updated
