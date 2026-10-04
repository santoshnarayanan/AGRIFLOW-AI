"""
AlertRepository — data access for the Alert domain.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AlertSeverity, AlertType
from app.db.models.alert import Alert
from app.db.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Alert, session)

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """Return all alerts for a field, ordered by triggered_at descending."""
        result = await self._session.execute(
            select(Alert)
            .where(Alert.field_id == field_id)
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_active_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """Return unacknowledged alerts for a field, most severe first."""
        result = await self._session.execute(
            select(Alert)
            .where(
                Alert.field_id == field_id,
                Alert.is_acknowledged.is_(False),
            )
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_severity(
        self,
        field_id: uuid.UUID,
        severity: AlertSeverity,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """Return alerts for a field filtered by severity."""
        result = await self._session.execute(
            select(Alert)
            .where(
                Alert.field_id == field_id,
                Alert.severity == severity,
            )
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_type(
        self,
        field_id: uuid.UUID,
        alert_type: AlertType,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """Return alerts for a field filtered by alert type."""
        result = await self._session.execute(
            select(Alert)
            .where(
                Alert.field_id == field_id,
                Alert.alert_type == alert_type,
            )
            .order_by(Alert.triggered_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> Alert:
        return await super().create(data)

    async def update(self, record_id: uuid.UUID, data: dict[str, Any]) -> Alert | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)
