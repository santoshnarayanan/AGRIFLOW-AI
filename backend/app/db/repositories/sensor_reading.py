"""
SensorReading repository.

Extends BaseRepository with telemetry-specific queries:

- ``list_by_field``  — full time-series of sensor readings for a given field,
                       ordered by recorded_at descending (most recent reading
                       first).  Pure DB predicate; no business logic.
                       Pagination is deferred per ADR-007-21.
- ``exists``         — lightweight existence probe that avoids hydrating the
                       full ORM instance when only presence needs to be
                       confirmed.

Inherited from BaseRepository:

Methods
-------
get_by_id   — fetch by primary key UUID (inherited)
create      — insert a new row from a field-value dict (inherited)
delete      — remove by primary key UUID, returns bool (inherited)

Immutability contract (ADR-007-19)
-----------------------------------
SensorReading is append-only telemetry.  ``update`` is intentionally NOT
surfaced in this repository.  It exists on the BaseRepository but must not
be called from the service layer — the immutability contract is enforced
there, consistent with ADR-007-17 (repository owns persistence, not
intelligence).  Telemetry corrections are expressed as new readings.

Event contract (ADR-007-20)
----------------------------
This repository is event-agnostic.  No Redpanda or event-bus publishing
occurs here.  Future CQRS projections or Digital Twin feeds are wired at
the service layer or in a dedicated event-publishing adapter.

Architecture readiness
----------------------
- TimescaleDB: ``list_by_field`` ordering by ``recorded_at`` DESC is the
  natural hypertable scan direction; partition key upgrade requires no
  query changes here.
- Cassandra: partition-by-field_id / cluster-by-recorded_at maps directly
  to the ``list_by_field`` access pattern.
- CQRS: ``create`` and ``delete`` are write-side operations; ``list_by_field``
  and ``get_by_id`` are read-side — splitting them across physical stores
  requires no contract change in the repository interface.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sensor_reading import SensorReading
from app.db.repositories.base import BaseRepository


class SensorReadingRepository(BaseRepository[SensorReading]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SensorReading, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> SensorReading | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> SensorReading:
        return await super().create(data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── SensorReading-specific queries ────────────────────────────────────────

    async def list_by_field(
        self,
        field_id: uuid.UUID,
    ) -> list[SensorReading]:
        """
        Return all sensor readings belonging to a field, ordered by
        recorded_at descending (most recent reading first).

        No pagination, date-range filtering, or aggregation is applied —
        all query refinements are deferred to future repository iterations
        per ADR-007-21.  The service layer is responsible for any downstream
        result processing.

        Ordering by ``recorded_at DESC`` is the canonical telemetry access
        pattern and maps directly to a TimescaleDB hypertable scan without
        structural change when that upgrade is made.
        """
        result = await self._session.execute(
            select(SensorReading)
            .where(SensorReading.field_id == field_id)
            .order_by(SensorReading.recorded_at.desc())
        )
        return list(result.scalars().all())

    async def exists(self, record_id: uuid.UUID) -> bool:
        """
        Return True if a SensorReading with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe for existence checks before performing
        delete operations; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(SensorReading.id).where(SensorReading.id == record_id)
        )
        return result.scalar_one_or_none() is not None
