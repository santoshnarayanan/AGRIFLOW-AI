"""Persistence for field dashboard CQRS read models."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.field_dashboard_read_model import FieldDashboardReadModel
from app.db.repositories.base import BaseRepository


class FieldDashboardReadModelRepository(BaseRepository[FieldDashboardReadModel]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(FieldDashboardReadModel, session)

    async def get_by_field_id(self, field_id: uuid.UUID) -> FieldDashboardReadModel | None:
        result = await self._session.execute(
            select(FieldDashboardReadModel).where(FieldDashboardReadModel.field_id == field_id)
        )
        return result.scalar_one_or_none()

    async def list_by_farm_id(self, farm_id: uuid.UUID) -> list[FieldDashboardReadModel]:
        result = await self._session.execute(
            select(FieldDashboardReadModel)
            .where(FieldDashboardReadModel.farm_id == farm_id)
            .order_by(FieldDashboardReadModel.field_name)
        )
        return list(result.scalars().all())

    async def list_all(self, *, limit: int = 5000) -> list[FieldDashboardReadModel]:
        result = await self._session.execute(
            select(FieldDashboardReadModel)
            .order_by(desc(FieldDashboardReadModel.refreshed_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def latest_refreshed_at(self) -> Any:
        result = await self._session.execute(
            select(FieldDashboardReadModel.refreshed_at)
            .order_by(desc(FieldDashboardReadModel.refreshed_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_rows(self) -> int:
        from sqlalchemy import func

        count_result = await self._session.execute(
            select(func.count()).select_from(FieldDashboardReadModel)
        )
        return int(count_result.scalar_one())

    async def count_with_feature_snapshot(self) -> int:
        from sqlalchemy import func

        result = await self._session.execute(
            select(func.count())
            .select_from(FieldDashboardReadModel)
            .where(FieldDashboardReadModel.feature_snapshot_id.is_not(None))
        )
        return int(result.scalar_one())

    async def upsert_for_field(
        self,
        field_id: uuid.UUID,
        data: dict[str, Any],
    ) -> FieldDashboardReadModel:
        existing = await self.get_by_field_id(field_id)
        if existing is None:
            return await self.create({"field_id": field_id, **data})
        updated = await self.update(existing.id, data)
        assert updated is not None
        return updated
