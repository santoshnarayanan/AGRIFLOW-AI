"""
IrrigationEvent repository.

Extends BaseRepository with irrigation-specific queries:

- ``list_by_field``  — paginated irrigation events for a given field, ordered
                       by started_at descending (most recent event first).
                       Pure DB predicate; no business logic.
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
list_by_field   — paginated irrigation events for a specific field,
                  most recent first (ordered by started_at DESC)
exists          — lightweight presence probe by primary key UUID

Query ordering
--------------
All list queries are ordered by ``started_at DESC``.  ``started_at`` is the
primary time key for IrrigationEvent (the TimescaleDB partition key and
Cassandra clustering key in future migrations).  Descending ordering reflects
the canonical operational access pattern: operators review the most recent
irrigation activity first.

Architecture readiness
----------------------
- TimescaleDB: ``list_by_field`` ordering by ``started_at DESC`` is the
  natural hypertable scan direction; the ``(field_id, started_at)`` compound
  index already established in the migration covers this access pattern.
- Cassandra: partition-by-field_id / cluster-by-started_at-DESC maps directly
  to the ``list_by_field`` access pattern.
- CQRS: ``create``, ``update``, and ``delete`` are write-side operations;
  ``list_by_field`` and ``get_by_id`` are read-side — splitting them across
  physical stores requires no contract change in the repository interface.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.irrigation_event import IrrigationEvent
from app.db.repositories.base import BaseRepository


class IrrigationEventRepository(BaseRepository[IrrigationEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(IrrigationEvent, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, record_id: uuid.UUID) -> IrrigationEvent | None:
        return await super().get_by_id(record_id)

    async def create(self, data: dict[str, Any]) -> IrrigationEvent:
        return await super().create(data)

    async def update(
        self,
        record_id: uuid.UUID,
        data: dict[str, Any],
    ) -> IrrigationEvent | None:
        return await super().update(record_id, data)

    async def delete(self, record_id: uuid.UUID) -> bool:
        return await super().delete(record_id)

    # ── IrrigationEvent-specific queries ──────────────────────────────────────

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IrrigationEvent]:
        """
        Return all irrigation events belonging to a field, ordered by
        started_at descending (most recent event first).

        ``limit`` and ``offset`` enable paginated access over large event
        histories without loading the full dataset into memory.  No filtering
        predicate beyond field ownership is applied here — the service layer is
        responsible for any date-range or method-based filtering.

        The ``(field_id, started_at)`` compound index established in the Phase 8
        migration covers this access pattern without a full table scan.
        """
        result = await self._session.execute(
            select(IrrigationEvent)
            .where(IrrigationEvent.field_id == field_id)
            .order_by(IrrigationEvent.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, record_id: uuid.UUID) -> bool:
        """
        Return True if an IrrigationEvent with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe for existence checks before performing
        update or delete operations; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(IrrigationEvent.id).where(IrrigationEvent.id == record_id)
        )
        return result.scalar_one_or_none() is not None
