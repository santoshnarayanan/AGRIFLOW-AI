"""Persistence for field feature snapshots."""

from __future__ import annotations

import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.db.repositories.base import BaseRepository


class FieldFeatureSnapshotRepository(BaseRepository[FieldFeatureSnapshot]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FieldFeatureSnapshot, session)

    async def get_latest_for_field(
        self,
        field_id: uuid.UUID,
        *,
        registry_version: str | None = None,
    ) -> FieldFeatureSnapshot | None:
        query = (
            select(FieldFeatureSnapshot)
            .where(FieldFeatureSnapshot.field_id == field_id)
            .order_by(desc(FieldFeatureSnapshot.as_of))
            .limit(1)
        )
        if registry_version:
            query = query.where(FieldFeatureSnapshot.registry_version == registry_version)
        result = await self._session.execute(query)
        return result.scalar_one_or_none()

    async def list_for_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[FieldFeatureSnapshot]:
        result = await self._session.execute(
            select(FieldFeatureSnapshot)
            .where(FieldFeatureSnapshot.field_id == field_id)
            .order_by(desc(FieldFeatureSnapshot.as_of))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
