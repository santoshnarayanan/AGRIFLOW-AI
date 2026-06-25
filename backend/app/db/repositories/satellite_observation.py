"""
SatelliteObservation repository.

Extends BaseRepository with satellite-observation-specific queries:

- ``list``                              — paginated global listing ordered by
                                          observed_at descending.
- ``list_by_field``                     — paginated field observation history,
                                          ordered by observed_at descending.
                                          Backed by the
                                          ``(field_id, observed_at)`` compound
                                          index.
- ``list_by_field_and_date_range``      — field observations within an inclusive
                                          observed_at window; primary access
                                          pattern for AI feature extraction and
                                          historical analytics.
- ``get_latest_by_field_and_spectral_index`` — most recent observation for a
                                          field and spectral index pair.
- ``list_by_field_and_spectral_index``  — index-specific time series for a
                                          field, ordered by observed_at
                                          descending.
- ``list_by_provider``                  — observations filtered by satellite
                                          provider; supports provider-scoped
                                          analytics and training data curation.
- ``list_by_processing_level``          — observations filtered by processing
                                          level; supports AI quality-gate
                                          queries (e.g. ARD/L2A training sets).
- ``exists``                            — lightweight existence probe that
                                          avoids hydrating the full ORM instance
                                          when only presence needs to be
                                          confirmed.

All write operations (create, update, delete) and get_by_id are inherited
from BaseRepository unchanged.

Methods
-------
get_by_id                              — fetch by primary key UUID (inherited)
create                                 — insert a new row from a field-value dict (inherited)
update                                 — sparse patch by primary key UUID (inherited)
delete                                 — remove by primary key UUID, returns bool (inherited)
list                                   — paginated global listing, observed_at DESC
list_by_field                          — paginated field history, observed_at DESC
list_by_field_and_date_range           — field history within an observed_at window
get_latest_by_field_and_spectral_index — latest observation for field + spectral index
list_by_field_and_spectral_index       — index-specific field time series
list_by_provider                       — observations filtered by satellite provider
list_by_processing_level               — observations filtered by processing level
exists                                 — lightweight presence probe by primary key UUID

Query ordering
--------------
All list queries are ordered by ``observed_at DESC``.  ``observed_at`` is the
primary time key for SatelliteObservation (the TimescaleDB partition key and
Cassandra clustering key in future migrations).  Descending ordering reflects
the canonical API access pattern: consumers review the most recent observation
first.  The service layer may reverse results when ascending chronological
order is required for feature-engineering pipelines.

Index coverage
--------------
- ``list_by_field``                     — uses
  ``ix_satellite_observations_field_id_observed_at`` compound index.
- ``list_by_field_and_date_range``      — uses
  ``ix_satellite_observations_field_id_observed_at`` (field_id leading column).
- ``list_by_field_and_spectral_index``  — uses
  ``ix_satellite_observations_field_id_observed_at`` with an additional
  spectral_index predicate.
- ``get_latest_by_field_and_spectral_index`` — same compound index; LIMIT 1
  after observed_at DESC ordering.
- ``list_by_provider``                  — uses
  ``ix_satellite_observations_satellite_provider``.
- ``list_by_processing_level``          — table scan with processing_level
  predicate; acceptable at current scale; a dedicated index can be added in a
  future migration if analytics volume requires it.

Architecture readiness
----------------------
- TimescaleDB: all time-ordered queries scan by ``observed_at DESC`` — the
  natural hypertable direction after partition promotion on ``observed_at``.
- Cassandra: partition-by-field_id / cluster-by-observed_at-DESC maps directly
  to the ``list_by_field`` and ``list_by_field_and_spectral_index`` access
  patterns.
- CQRS: ``create``, ``update``, and ``delete`` are write-side operations;
  all query methods are read-side — splitting them across physical stores
  requires no contract change in the repository interface.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.db.models.satellite_observation import SatelliteObservation
from app.db.repositories.base import BaseRepository


class SatelliteObservationRepository(BaseRepository[SatelliteObservation]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(SatelliteObservation, session)

    # ── Inherited from BaseRepository (typed here for clarity) ────────────────

    async def get_by_id(self, observation_id: uuid.UUID) -> SatelliteObservation | None:
        return await super().get_by_id(observation_id)

    async def create(self, data: dict[str, Any]) -> SatelliteObservation:
        return await super().create(data)

    async def update(
        self,
        observation_id: uuid.UUID,
        data: dict[str, Any],
    ) -> SatelliteObservation | None:
        return await super().update(observation_id, data)

    async def delete(self, observation_id: uuid.UUID) -> bool:
        return await super().delete(observation_id)

    # ── SatelliteObservation-specific queries ─────────────────────────────────

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return a paginated list of all satellite observations, ordered by
        observed_at descending (most recent observation first).

        ``limit`` and ``offset`` enable paginated access over large datasets
        without loading the full table into memory.  No filtering predicate is
        applied — the service layer is responsible for any domain-specific
        filtering before returning results to API consumers.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .order_by(SatelliteObservation.observed_at.desc())
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
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations belonging to a field, ordered by
        observed_at descending (most recent observation first).

        This is the primary API access pattern for field observation history
        (GET /fields/{field_id}/satellite-observations).  The
        ``ix_satellite_observations_field_id_observed_at`` compound index
        established in migration a1b2c3d4e5f6 covers this query without a full
        table scan.

        ``limit`` and ``offset`` enable paginated access over long-running
        satellite time series without loading the full history into memory.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(SatelliteObservation.field_id == field_id)
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_field_and_date_range(
        self,
        field_id: uuid.UUID,
        start: datetime,
        end: datetime,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return satellite observations for a field within an inclusive
        ``observed_at`` window, ordered by observed_at descending.

        ``start`` and ``end`` must be timezone-aware datetimes; timezone
        validation is the responsibility of the service layer.  This query
        supports AI feature extraction (growing-season NDVI windows), historical
        analytics, and Digital Twin state reconstruction.

        The ``ix_satellite_observations_field_id_observed_at`` compound index
        covers the field_id predicate; the observed_at range filter is applied
        as an additional predicate on the indexed column.

        No cloud-cover or processing-level filtering is applied here — those
        quality gates belong to the service layer or the AI pipeline.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(
                SatelliteObservation.field_id == field_id,
                SatelliteObservation.observed_at >= start,
                SatelliteObservation.observed_at <= end,
            )
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_latest_by_field_and_spectral_index(
        self,
        field_id: uuid.UUID,
        spectral_index: SpectralIndex,
    ) -> SatelliteObservation | None:
        """
        Return the most recent satellite observation for a field and spectral
        index pair, or None if no matching observation exists.

        Uses ``LIMIT 1`` after ``observed_at DESC`` ordering.  This query
        supports Digital Twin current-state updates (latest NDVI canopy health,
        latest NDWI water-stress signal) and real-time analytics dashboards.

        The ``ix_satellite_observations_field_id_observed_at`` compound index
        with an additional spectral_index predicate covers this access pattern.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(
                SatelliteObservation.field_id == field_id,
                SatelliteObservation.spectral_index == spectral_index,
            )
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_by_field_and_spectral_index(
        self,
        field_id: uuid.UUID,
        spectral_index: SpectralIndex,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations for a field filtered by spectral
        index, ordered by observed_at descending (most recent first).

        This is the index-specific field history query — for example, retrieving
        the full NDVI time series for a field to assemble a growing-season
        feature vector for the Phase 12 Yield Prediction Engine.

        The ``ix_satellite_observations_field_id_observed_at`` compound index
        covers the field_id predicate; spectral_index is applied as an
        additional filter predicate.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(
                SatelliteObservation.field_id == field_id,
                SatelliteObservation.spectral_index == spectral_index,
            )
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_provider(
        self,
        satellite_provider: SatelliteProvider,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations sourced from a given satellite
        provider, ordered by observed_at descending.

        Supports provider-scoped analytics, training data curation, and
        resolution-aware feature engineering (e.g. isolating Sentinel-2 10 m
        observations from MODIS 250 m observations before model training).

        The ``ix_satellite_observations_satellite_provider`` index established
        in migration a1b2c3d4e5f6 covers this access pattern.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(SatelliteObservation.satellite_provider == satellite_provider)
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_processing_level(
        self,
        processing_level: ProcessingLevel,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations at a given processing level, ordered
        by observed_at descending.

        Supports AI quality-gate queries — for example, retrieving all ARD or
        L2A observations suitable for multi-temporal model training while
        excluding top-of-atmosphere L1C products.

        No additional quality predicates (cloud cover, resolution) are applied
        here; those filters belong to the service layer or the feature pipeline.
        """
        result = await self._session.execute(
            select(SatelliteObservation)
            .where(SatelliteObservation.processing_level == processing_level)
            .order_by(SatelliteObservation.observed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def exists(self, observation_id: uuid.UUID) -> bool:
        """
        Return True if a SatelliteObservation with the given UUID exists.

        Uses a SELECT on the primary key column only — avoids hydrating the
        full ORM instance when only presence needs to be confirmed.  The
        service layer uses this probe for existence checks before performing
        update or delete operations; no business rule is encoded here.
        """
        result = await self._session.execute(
            select(SatelliteObservation.id).where(
                SatelliteObservation.id == observation_id
            )
        )
        return result.scalar_one_or_none() is not None
