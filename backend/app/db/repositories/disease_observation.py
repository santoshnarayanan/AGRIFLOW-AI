"""
DiseaseObservation repository.

Extends BaseRepository with disease-observation-specific queries:

- ``get_by_crop``   — paginated disease observations for a given crop cycle,
                      ordered by observed_at descending (most recent observation
                      first).  Backed by the ``(crop_id, observed_at)`` compound
                      index.
- ``get_by_field``  — paginated disease observations for a given field across
                      all crop cycles, ordered by observed_at descending.
                      Backed by the ``ix_disease_observations_field_id`` index.

All write operations (create, update, delete) and get_by_id are inherited
from BaseRepository unchanged.

Methods
-------
get_by_id       — fetch by primary key UUID (inherited)
create          — insert a new row from a field-value dict (inherited)
update          — sparse patch by primary key UUID (inherited)
delete          — remove by primary key UUID, returns bool (inherited)
get_by_crop     — paginated disease observations for a specific crop cycle,
                  most recent first (ordered by observed_at DESC)
get_by_field    — paginated disease observations for a specific field across
                  all crop cycles, most recent first (ordered by observed_at DESC)

Query ordering
--------------
All list queries are ordered by ``observed_at DESC``.  ``observed_at`` is the
primary time key for DiseaseObservation (the TimescaleDB partition key and
Cassandra clustering key in future migrations).  Descending ordering reflects
the canonical access pattern: consumers review the most recent disease
observation first.

Index coverage
--------------
- ``get_by_crop``  — uses the ``(crop_id, observed_at)`` compound index
  established in migration d3e7b2a9f1c4.  This is the primary AI feature
  pipeline access pattern for the Phase 13 Disease Risk Scoring Engine.
- ``get_by_field`` — uses the ``ix_disease_observations_field_id`` single-column
  index.  Enables direct field-scoped queries without a JOIN through crops,
  consistent with the field_id denormalization decision (ADR-009-02).

Architecture readiness
----------------------
- TimescaleDB: both list queries order by ``observed_at DESC`` — the natural
  hypertable scan direction after partition promotion on ``observed_at``.
- Cassandra: partition-by-crop_id / cluster-by-observed_at-DESC maps directly
  to the ``get_by_crop`` access pattern.
- CQRS: ``create``, ``update``, and ``delete`` are write-side operations;
  ``get_by_crop``, ``get_by_field``, and ``get_by_id`` are read-side —
  splitting them across physical stores requires no contract change.
"""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.disease_observation import DiseaseObservation
from app.db.repositories.base import BaseRepository


class DiseaseObservationRepository(BaseRepository[DiseaseObservation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DiseaseObservation, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, observation_id: uuid.UUID) -> DiseaseObservation | None:
        return await super().get_by_id(observation_id)

    async def create(self, data: dict[str, Any]) -> DiseaseObservation:
        return await super().create(data)

    async def update(
        self,
        observation_id: uuid.UUID,
        data: dict[str, Any],
    ) -> DiseaseObservation | None:
        return await super().update(observation_id, data)

    async def delete(self, observation_id: uuid.UUID) -> bool:
        return await super().delete(observation_id)

    # ── DiseaseObservation-specific queries ───────────────────────────────────

    async def get_by_crop(
        self,
        crop_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DiseaseObservation]:
        """
        Return all disease observations belonging to a crop cycle, ordered by
        observed_at descending (most recent observation first).

        ``limit`` and ``offset`` enable paginated access over large observation
        histories without loading the full dataset into memory.  No filtering
        predicate beyond crop ownership is applied here — the service layer is
        responsible for any date-range or severity-based filtering.

        The ``(crop_id, observed_at)`` compound index established in migration
        d3e7b2a9f1c4 covers this access pattern without a full table scan.
        This is the primary query path for the Phase 13 Disease Risk Scoring
        Engine feature vector assembly.
        """
        result = await self._session.execute(
            select(DiseaseObservation)
            .where(DiseaseObservation.crop_id == crop_id)
            .order_by(DiseaseObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DiseaseObservation]:
        """
        Return all disease observations for a field across all crop cycles,
        ordered by observed_at descending (most recent observation first).

        This query uses the denormalized ``field_id`` column (ADR-009-02) to
        avoid a JOIN through the ``crops`` table, enabling direct field-scoped
        access consistent with the pattern used by all other Field child
        domains (SensorReading, IrrigationEvent, WeatherRecord, YieldRecord).

        The ``ix_disease_observations_field_id`` index established in migration
        d3e7b2a9f1c4 covers this access pattern.  This endpoint is also the
        backing query for the GaaS PlantHealthAdvisor tool layer (future).
        """
        result = await self._session.execute(
            select(DiseaseObservation)
            .where(DiseaseObservation.field_id == field_id)
            .order_by(DiseaseObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
