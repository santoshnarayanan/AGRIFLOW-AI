"""
YieldRecord repository.

Extends BaseRepository with yield-specific queries:

- ``list_by_crop``   — paginated yield records for a given crop cycle, ordered
                       by recorded_at descending (most recent measurement first).
                       Backed by the ``(crop_id, recorded_at)`` compound index.
- ``list_by_field``  — paginated yield records for a given field across all crop
                       cycles, ordered by recorded_at descending.
                       Backed by the ``ix_yield_records_field_id`` index.
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
delete          — remove by primary key UUID, returns bool (inherited)
list_by_crop    — paginated yield records for a specific crop cycle,
                  most recent first (ordered by recorded_at DESC)
list_by_field   — paginated yield records for a specific field across all
                  crop cycles, most recent first (ordered by recorded_at DESC)
exists          — lightweight presence probe by primary key UUID

Query ordering
--------------
All list queries are ordered by ``recorded_at DESC``.  ``recorded_at`` is the
primary time key for YieldRecord (the TimescaleDB partition key and Cassandra
clustering key in future migrations).  Descending ordering reflects the
canonical access pattern: consumers review the most recent yield observation
first.

Index coverage
--------------
- ``list_by_crop``  — uses the ``(crop_id, recorded_at)`` compound index
  established in migration b7e2a9f4c8d3.  This is the primary AI feature
  pipeline access pattern for the Phase 12 Yield Prediction Engine.
- ``list_by_field`` — uses the ``ix_yield_records_field_id`` single-column
  index.  Enables direct field-scoped queries without a JOIN through crops,
  consistent with the field_id denormalization decision (ADR-009-02).

Architecture readiness
----------------------
- TimescaleDB: both list queries order by ``recorded_at DESC`` — the natural
  hypertable scan direction after partition promotion on ``recorded_at``.
- Cassandra: partition-by-crop_id / cluster-by-recorded_at-DESC maps directly
  to the ``list_by_crop`` access pattern.
- CQRS: ``create``, ``update``, and ``delete`` are write-side operations;
  ``list_by_crop``, ``list_by_field``, and ``get_by_id`` are read-side —
  splitting them across physical stores requires no contract change.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.yield_record import YieldRecord
from app.db.repositories.base import BaseRepository


class YieldRecordRepository(BaseRepository[YieldRecord]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(YieldRecord, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> YieldRecord | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> YieldRecord:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> YieldRecord | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── YieldRecord-specific queries ──────────────────────────────────────────

    async def list_by_crop(
        self,
        crop_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[YieldRecord]:
        """
        Return all yield records belonging to a crop cycle, ordered by
        recorded_at descending (most recent measurement first).

        ``limit`` and ``offset`` enable paginated access over large yield
        histories without loading the full dataset into memory.  No filtering
        predicate beyond crop ownership is applied here — the service layer is
        responsible for any date-range or method-based filtering.

        The ``(crop_id, recorded_at)`` compound index established in migration
        b7e2a9f4c8d3 covers this access pattern without a full table scan.
        This is the primary query path for the Phase 12 Yield Prediction Engine
        feature vector assembly.
        """
        result = await self._session.execute(
            select(YieldRecord)
            .where(YieldRecord.crop_id == crop_id)
            .order_by(YieldRecord.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[YieldRecord]:
        """
        Return all yield records for a field across all crop cycles, ordered by
        recorded_at descending (most recent measurement first).

        This query uses the denormalized ``field_id`` column (ADR-009-02) to
        avoid a JOIN through the ``crops`` table, enabling direct field-scoped
        access consistent with the pattern used by all other Field child
        domains (SensorReading, IrrigationEvent, WeatherRecord).

        The ``ix_yield_records_field_id`` index established in migration
        b7e2a9f4c8d3 covers this access pattern.  This endpoint is also the
        backing query for the GaaS YieldAdvisor tool layer (future).
        """
        result = await self._session.execute(
            select(YieldRecord)
            .where(YieldRecord.field_id == field_id)
            .order_by(YieldRecord.recorded_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, record_id: uuid.UUID) -> bool:
        """
        Return True if a YieldRecord with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe for existence checks before performing
        update or delete operations; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(YieldRecord.id).where(YieldRecord.id == record_id)
        )
        return result.scalar_one_or_none() is not None
