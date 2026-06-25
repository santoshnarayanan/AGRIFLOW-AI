"""
SatelliteObservationService — business logic for the SatelliteObservation domain.

Responsibilities
----------------
- Verify the parent field exists before creating an observation.           (rule 1)
- Ensure observed_at is not in the future.                                 (rule 2)
- Validate index_value against spectral_index contextual bounds.           (rule 3)
- Ensure resolution_m is > 0 when supplied.                                (rule 4)
- Ensure cloud_cover_percent is in [0, 100] when supplied.                 (rule 5)
- Ensure start <= end for date-range queries.                              (rule 6)
- Verify an observation exists before applying an update.                  (rule 7)
- Verify an observation exists before deletion.                            (rule 8)

Validation delegation
---------------------
The following invariants are enforced by the Pydantic schema layer and are
NOT re-validated here unless defence-in-depth is warranted for programmatic
callers that bypass the schema layer:

- Timezone-awareness of ``observed_at``         — ``@field_validator`` on
  SatelliteObservationCreate and SatelliteObservationUpdate.
- ``index_value >= -1``                           — ``ge=-1`` on both schemas.
- ``cloud_cover_percent`` in [0, 100]             — ``ge=0, le=100`` on both schemas.
- ``resolution_m >= 0``                           — ``ge=0`` on both schemas.
- ``scene_id`` max 255 characters                 — ``max_length=255`` on both schemas.
- ``source_url`` max 500 characters               — ``max_length=500`` on both schemas.

The service layer adds:
- The future-timestamp guard (rule 2) — requires UTC clock comparison that
  Pydantic cannot safely perform.
- Per-index ``index_value`` upper-bound guards (rule 3) — contextual bounds
  depend on ``spectral_index`` and cannot be expressed as a single schema
  constraint.
- ``resolution_m > 0`` when supplied (rule 4) — zero resolution is physically
  invalid; Pydantic allows exactly zero (ge=0) but the service tightens this,
  matching the YieldRecord ``area_harvested_ha`` pattern.

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.  This mirrors the
``FieldNotFoundError`` reuse pattern in ``IrrigationEventService`` and
``SensorReadingService``.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.enums import ProcessingLevel, SatelliteProvider, SpectralIndex
from app.core.logging.logger import get_logger
from app.db.models.satellite_observation import SatelliteObservation
from app.db.repositories.field import FieldRepository
from app.db.repositories.satellite_observation import SatelliteObservationRepository
from app.schemas.satellite_observation import (
    SatelliteObservationCreate,
    SatelliteObservationUpdate,
)
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Spectral index validation registry ────────────────────────────────────────

# Ratio-based vegetation and water indices are bounded to [-1.0, 1.0] by their
# mathematical construction.  New ratio indices should be added here when the
# SpectralIndex enum is extended.
_BOUNDED_SPECTRAL_INDICES: frozenset[SpectralIndex] = frozenset(
    {
        SpectralIndex.NDVI,
        SpectralIndex.EVI,
        SpectralIndex.NDWI,
        SpectralIndex.SAVI,
        SpectralIndex.NDRE,
        SpectralIndex.MSAVI,
        SpectralIndex.GNDVI,
    }
)

# LAI is not ratio-bounded; typical canopy values are positive and rarely exceed
# ~10 in dense tropical canopies.  An upper bound is not enforced here to
# avoid blocking valid scientific observations; AI pipelines may apply tighter
# gates downstream.
_POSITIVE_SPECTRAL_INDICES: frozenset[SpectralIndex] = frozenset({SpectralIndex.LAI})


# ── Domain exceptions ──────────────────────────────────────────────────────────


class SatelliteObservationNotFoundError(ValueError):
    """Raised when the referenced satellite observation does not exist."""


class InvalidSatelliteObservationError(ValueError):
    """
    Raised when a satellite observation value violates domain business rules
    at the service layer.

    Invariants enforced here that Pydantic cannot cover alone:

    1. ``observed_at`` must not be in the future — satellite observations
       represent past or present Earth-observation events.

    2. ``index_value`` must fall within the contextual range for the selected
       ``spectral_index`` — ratio indices in [-1.0, 1.0]; LAI must be > 0.

    3. ``resolution_m``, when supplied, must be > 0 — zero pixel resolution
       is physically invalid.

    4. ``cloud_cover_percent``, when supplied, must be in [0, 100].

    5. Date-range query ``start`` must not be after ``end``.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class SatelliteObservationService:
    """
    Encapsulates all business logic for SatelliteObservation operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        satellite_observation_repository: SatelliteObservationRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._observations = satellite_observation_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_satellite_observation(
        self,
        field_id: uuid.UUID,
        payload: SatelliteObservationCreate,
    ) -> SatelliteObservation:
        """
        Persist a new satellite observation for the given field.

        Validates parent field existence, timestamp, index value, resolution,
        and cloud cover before delegating persistence to the repository.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        InvalidSatelliteObservationError
            If ``observed_at`` is in the future, ``index_value`` is outside
            the contextual range for ``spectral_index``, ``resolution_m`` is
            supplied and <= 0, or ``cloud_cover_percent`` is outside [0, 100].
        """
        log = logger.bind(
            field_id=str(field_id),
            spectral_index=payload.spectral_index.value,
            satellite_provider=payload.satellite_provider.value,
        )

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("satellite_observation_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 2 — observed_at must not be in the future
        _validate_observed_at_not_future(observed_at=payload.observed_at, log=log)

        # Rule 3 — contextual index value bounds
        _validate_index_value(
            spectral_index=payload.spectral_index,
            index_value=payload.index_value,
            log=log,
        )

        # Rule 4 — resolution must be > 0 when supplied
        _validate_resolution(resolution_m=payload.resolution_m, log=log)

        # Rule 5 — cloud cover bounds (defence-in-depth)
        _validate_cloud_cover(
            cloud_cover_percent=payload.cloud_cover_percent,
            log=log,
        )

        data: dict[str, Any] = {
            "field_id": field_id,
            **payload.model_dump(),
        }
        observation = await self._observations.create(data)
        log.info(
            "satellite_observation_service.create.success",
            observation_id=str(observation.id),
        )

        # ── Future extension point ─────────────────────────────────────────────
        # This is the intended boundary for the following integrations.
        # Do NOT implement here; wire in a dedicated event-publishing adapter:
        #
        # - SatelliteObservationCreated event → Redpanda / Kafka topic
        # - Digital Twin field canopy health state update
        # - CQRS read-model projection
        # - Phase 12 Yield Prediction Engine feature pipeline trigger
        # - Phase 13 Disease Risk Engine NDRE/NDVI signal trigger
        # - Phase 14 Irrigation Recommendation NDWI signal trigger
        # - GaaS SatelliteAdvisor tool layer
        # ──────────────────────────────────────────────────────────────────────

        return observation

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_satellite_observation(
        self,
        observation_id: uuid.UUID,
    ) -> SatelliteObservation | None:
        """
        Return a single satellite observation by primary key.

        Returns ``None`` when no observation with ``observation_id`` exists so
        that callers can decide whether a missing resource is an error
        (e.g. raise HTTP 404 in the router layer).
        """
        observation = await self._observations.get_by_id(observation_id)
        if observation is None:
            logger.bind(observation_id=str(observation_id)).debug(
                "satellite_observation_service.get.not_found"
            )
        return observation

    async def list_satellite_observations(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return a paginated list of all satellite observations, ordered by
        observed_at descending (most recent observation first).

        Delegates filtering and ordering to ``SatelliteObservationRepository.list``.
        """
        return await self._observations.list(limit=limit, offset=offset)

    async def list_field_satellite_observations(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations belonging to a field, ordered by
        observed_at descending (most recent observation first).

        Primary access pattern for field observation history and Digital Twin
        field-level canopy health timelines.
        """
        return await self._observations.list_by_field(
            field_id,
            limit=limit,
            offset=offset,
        )

    async def list_field_satellite_observations_by_date_range(
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
        ``observed_at`` window.

        Supports AI feature extraction (growing-season NDVI windows), historical
        analytics, and model training dataset assembly.

        Raises
        ------
        InvalidSatelliteObservationError
            If ``start`` is after ``end``.
        """
        log = logger.bind(
            field_id=str(field_id),
            start=start.isoformat(),
            end=end.isoformat(),
        )
        _validate_date_range(start=start, end=end, log=log)

        return await self._observations.list_by_field_and_date_range(
            field_id,
            start,
            end,
            limit=limit,
            offset=offset,
        )

    async def get_latest_field_spectral_index_observation(
        self,
        field_id: uuid.UUID,
        spectral_index: SpectralIndex,
    ) -> SatelliteObservation | None:
        """
        Return the most recent satellite observation for a field and spectral
        index pair, or ``None`` if no matching observation exists.

        Supports Digital Twin current-state updates (latest NDVI canopy health,
        latest NDWI water-stress signal) and real-time analytics dashboards.
        """
        return await self._observations.get_latest_by_field_and_spectral_index(
            field_id,
            spectral_index,
        )

    async def list_field_spectral_index_history(
        self,
        field_id: uuid.UUID,
        spectral_index: SpectralIndex,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations for a field filtered by spectral
        index, ordered by observed_at descending.

        Primary access pattern for growing-season feature vector assembly in
        the Phase 12 Yield Prediction Engine and early-stress signal extraction
        in the Phase 13 Disease Risk Engine.
        """
        return await self._observations.list_by_field_and_spectral_index(
            field_id,
            spectral_index,
            limit=limit,
            offset=offset,
        )

    async def list_satellite_observations_by_provider(
        self,
        satellite_provider: SatelliteProvider,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations sourced from a given provider.

        Supports provider-scoped analytics and resolution-aware training data
        curation (e.g. isolating Sentinel-2 10 m observations from MODIS 250 m
        observations before model training).
        """
        return await self._observations.list_by_provider(
            satellite_provider,
            limit=limit,
            offset=offset,
        )

    async def list_satellite_observations_by_processing_level(
        self,
        processing_level: ProcessingLevel,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SatelliteObservation]:
        """
        Return all satellite observations at a given processing level.

        Supports AI quality-gate queries — for example, retrieving all ARD or
        L2A observations suitable for multi-temporal model training while
        excluding top-of-atmosphere L1C products.
        """
        return await self._observations.list_by_processing_level(
            processing_level,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_satellite_observation(
        self,
        observation_id: uuid.UUID,
        payload: SatelliteObservationUpdate,
    ) -> SatelliteObservation:
        """
        Apply a partial update to an existing satellite observation.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.

        ``field_id`` is immutable after creation and is excluded from
        ``SatelliteObservationUpdate`` at the schema level.  The repository's
        sparse-patch approach (``exclude_unset=True``) means ``field_id`` cannot
        be accidentally overwritten.

        Raises
        ------
        SatelliteObservationNotFoundError
            If no observation with ``observation_id`` exists.
        InvalidSatelliteObservationError
            If the supplied ``observed_at`` is in the future, the effective
            ``index_value`` is outside the contextual range for the effective
            ``spectral_index``, ``resolution_m`` is supplied and <= 0, or
            ``cloud_cover_percent`` is outside [0, 100].
        """
        log = logger.bind(observation_id=str(observation_id))

        # Rule 7 — observation must exist before update
        current = await self._observations.get_by_id(observation_id)
        if current is None:
            log.warning("satellite_observation_service.update.not_found")
            raise SatelliteObservationNotFoundError(
                f"Satellite observation '{observation_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 2 — validate future guard only if the caller is changing observed_at
        if "observed_at" in update_data:
            _validate_observed_at_not_future(
                observed_at=update_data["observed_at"],
                log=log,
            )

        # Rule 3 — validate index value against effective spectral index when
        # either discriminator or value is being changed
        if "index_value" in update_data or "spectral_index" in update_data:
            effective_spectral_index = update_data.get(
                "spectral_index", current.spectral_index
            )
            effective_index_value = update_data.get("index_value", current.index_value)
            _validate_index_value(
                spectral_index=effective_spectral_index,
                index_value=effective_index_value,
                log=log,
            )

        # Rule 4 — validate resolution only for fields being changed
        if "resolution_m" in update_data:
            _validate_resolution(resolution_m=update_data["resolution_m"], log=log)

        # Rule 5 — validate cloud cover only for fields being changed
        if "cloud_cover_percent" in update_data:
            _validate_cloud_cover(
                cloud_cover_percent=update_data["cloud_cover_percent"],
                log=log,
            )

        updated = await self._observations.update(observation_id, update_data)
        log.info("satellite_observation_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_satellite_observation(self, observation_id: uuid.UUID) -> bool:
        """
        Permanently remove a satellite observation.

        Returns ``True`` when the observation was deleted, ``False`` when no
        observation with ``observation_id`` exists.  The router layer is
        responsible for translating ``False`` into an appropriate HTTP response.
        """
        log = logger.bind(observation_id=str(observation_id))

        deleted = await self._observations.delete(observation_id)
        if not deleted:
            log.warning("satellite_observation_service.delete.not_found")
            return False

        log.info("satellite_observation_service.delete.success")
        return True


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_observed_at_not_future(
    *,
    observed_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidSatelliteObservationError`` if ``observed_at`` is in the future.

    The comparison is performed in UTC regardless of the incoming timezone so
    that observations from fields in non-UTC offsets are evaluated correctly.
    Pydantic already guarantees timezone-awareness at this point, so the
    naive-datetime branch (``replace(tzinfo=timezone.utc)``) is retained as a
    defence-in-depth guard for programmatic callers that bypass the schema layer.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    now_utc = datetime.now(timezone.utc)
    observed_at_utc = (
        observed_at.replace(tzinfo=timezone.utc)
        if observed_at.tzinfo is None
        else observed_at.astimezone(timezone.utc)
    )
    if observed_at_utc > now_utc:
        log.warning(
            "satellite_observation_service.timestamp_future",
            observed_at=observed_at.isoformat(),
        )
        raise InvalidSatelliteObservationError(
            f"observed_at ({observed_at.isoformat()}) cannot be in the future."
        )


def _validate_index_value(
    *,
    spectral_index: SpectralIndex,
    index_value: Decimal,
    log: Any,
) -> None:
    """
    Raise ``InvalidSatelliteObservationError`` if ``index_value`` is outside the
    contextual range for ``spectral_index``.

    Ratio-based indices (NDVI, EVI, NDWI, SAVI, NDRE, MSAVI, GNDVI) are bounded
    to [-1.0, 1.0] by their mathematical construction.  LAI must be positive.
    New ``SpectralIndex`` values should be registered in
    ``_BOUNDED_SPECTRAL_INDICES`` or ``_POSITIVE_SPECTRAL_INDICES`` above.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if spectral_index in _BOUNDED_SPECTRAL_INDICES:
        if index_value < Decimal("-1") or index_value > Decimal("1"):
            log.warning(
                "satellite_observation_service.index_value_out_of_range",
                spectral_index=spectral_index.value,
                index_value=str(index_value),
            )
            raise InvalidSatelliteObservationError(
                f"index_value ({index_value}) for spectral index "
                f"'{spectral_index.value}' must be in the range [-1.0, 1.0]."
            )
        return

    if spectral_index in _POSITIVE_SPECTRAL_INDICES:
        if index_value <= Decimal("0"):
            log.warning(
                "satellite_observation_service.index_value_not_positive",
                spectral_index=spectral_index.value,
                index_value=str(index_value),
            )
            raise InvalidSatelliteObservationError(
                f"index_value ({index_value}) for spectral index "
                f"'{spectral_index.value}' must be greater than zero."
            )


def _validate_resolution(
    *,
    resolution_m: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidSatelliteObservationError`` if ``resolution_m`` is supplied
    and is not greater than zero.

    Pydantic's ``ge=0`` constraint allows exactly zero, but zero pixel resolution
    is physically invalid — it cannot represent a real satellite product.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if resolution_m is not None and resolution_m <= 0:
        log.warning(
            "satellite_observation_service.invalid_resolution",
            resolution_m=str(resolution_m),
        )
        raise InvalidSatelliteObservationError(
            f"resolution_m ({resolution_m}) must be greater than zero when supplied."
        )


def _validate_cloud_cover(
    *,
    cloud_cover_percent: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidSatelliteObservationError`` if ``cloud_cover_percent`` is
    supplied and outside [0, 100].

    Also enforced at the schema layer; this helper provides defence-in-depth
    for programmatic callers that bypass Pydantic validation.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if cloud_cover_percent is not None and not (
        Decimal("0") <= cloud_cover_percent <= Decimal("100")
    ):
        log.warning(
            "satellite_observation_service.invalid_cloud_cover",
            cloud_cover_percent=str(cloud_cover_percent),
        )
        raise InvalidSatelliteObservationError(
            f"cloud_cover_percent ({cloud_cover_percent}) must be in the range [0, 100]."
        )


def _validate_date_range(
    *,
    start: datetime,
    end: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidSatelliteObservationError`` if ``start`` is after ``end``.

    Date-range queries with an inverted window would return empty results
    silently; rejecting the invalid range at the service layer gives callers a
    clear error before an unnecessary repository round-trip.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    start_utc = (
        start.replace(tzinfo=timezone.utc)
        if start.tzinfo is None
        else start.astimezone(timezone.utc)
    )
    end_utc = (
        end.replace(tzinfo=timezone.utc)
        if end.tzinfo is None
        else end.astimezone(timezone.utc)
    )
    if start_utc > end_utc:
        log.warning(
            "satellite_observation_service.invalid_date_range",
            start=start.isoformat(),
            end=end.isoformat(),
        )
        raise InvalidSatelliteObservationError(
            f"start ({start.isoformat()}) must not be after end ({end.isoformat()})."
        )
