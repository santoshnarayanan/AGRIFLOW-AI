"""
WeatherRecord repository.

Extends BaseRepository with weather-specific queries:

- ``list_by_field``  — paginated time-series of weather observations for a
                       given field, ordered by recorded_at descending (most
                       recent observation first).  Pure DB predicate; no
                       business logic.
- ``exists``         — lightweight existence probe that avoids hydrating the
                       full ORM instance when only presence needs to be
                       confirmed.

All write operations (create, update, delete) and get_by_id are inherited
from BaseRepository unchanged.

Methods
-------
get_by_id       — fetch by primary key UUID (inherited)
create          — insert a new row from a field-value dict (inherited)
update          — sparse patch by primary key UUID (inherited)
delete          — remove by primary key UUID (inherited)
list_by_field   — paginated weather observations for a specific field,
                  most recent first
exists          — lightweight presence probe by primary key UUID
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.weather_record import WeatherRecord
from app.db.repositories.base import BaseRepository


class WeatherRecordRepository(BaseRepository[WeatherRecord]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(WeatherRecord, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> WeatherRecord | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> WeatherRecord:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> WeatherRecord | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── WeatherRecord-specific queries ────────────────────────────────────────

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WeatherRecord]:
        """
        Return all weather observations belonging to a field, ordered by
        recorded_at descending (most recent observation first).

        ``limit`` and ``offset`` enable paginated access over large time-series
        datasets without loading the full history into memory.  No filtering
        predicate beyond field ownership is applied here — the service layer is
        responsible for any date-range or metric-based filtering.
        """
        result = await self._session.execute(
            select(WeatherRecord)
            .where(WeatherRecord.field_id == field_id)
            .order_by(WeatherRecord.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, record_id: uuid.UUID) -> bool:
        """
        Return True if a WeatherRecord with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe for ownership and existence checks before
        performing update or delete operations; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(WeatherRecord.id).where(WeatherRecord.id == record_id)
        )
        return result.scalar_one_or_none() is not None
