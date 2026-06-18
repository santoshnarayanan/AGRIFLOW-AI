"""
SensorReadingService — business logic for the SensorReading domain.

Responsibilities
----------------
- Verify the parent field exists before creating a sensor reading.       (rule 1)
- Verify a sensor reading exists before retrieval by ID.                 (rule 2)
- Verify the parent field exists before listing its readings.            (rule 3)
- Verify a sensor reading exists before deletion.                        (rule 4)
- Ensure recorded_at is timezone-aware — naive datetimes are rejected.  (rule 5)
- Ensure recorded_at is not in the future.                              (rule 6)

Intentionally absent
--------------------
- No sensor value range validation.  Physical plausibility rules (e.g.
  humidity in [0, 100], temperature bounds) belong to the future Telemetry
  Ingestion service and SensorDevice domain — they are sensor_type-specific
  and cannot be expressed as universal constraints here.

Immutability contract (ADR-007-27)
-----------------------------------
SensorReading is append-only telemetry.  There is no ``update_sensor_reading``
method.  Historical readings cannot be mutated.  Corrections are represented
as new readings; the record of what the sensor reported is preserved intact.

Event boundary (ADR-007-26)
-----------------------------
This service is the intended future integration boundary for:
- Redpanda / Kafka event publishing
- CQRS read-model projection triggers
- Digital Twin state updates
- TimescaleDB / Cassandra replication pipelines
- Generative-As-A-Service (GaaS) orchestration
- Temporal workflow initiation
None of these are implemented here.  See the ``create_sensor_reading`` method
for the designated extension point comment.

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.sensor_reading import SensorReading
from app.db.repositories.field import FieldRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.schemas.sensor_reading import SensorReadingCreate
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class SensorReadingNotFoundError(ValueError):
    """Raised when the referenced sensor reading does not exist."""


class InvalidSensorTimestampError(ValueError):
    """
    Raised when ``recorded_at`` is timezone-naive or set to a future timestamp.

    Two invariants are enforced (ADR-007-24, ADR-007-25):

    1. Timezone awareness — ``recorded_at`` must carry explicit timezone
       information.  A naive datetime (e.g. ``datetime.now()``) is ambiguous
       and cannot be safely compared across sensors in different UTC offsets.

    2. No future timestamps — sensor readings represent past or present
       physical observations.  A future ``recorded_at`` would corrupt
       time-series ordering, skew AI feature pipelines, and produce
       misleading Digital Twin state.

    Both invariants are enforced here at the service layer rather than in the
    database so that callers receive a meaningful error message rather than a
    TIMESTAMPTZ constraint violation.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class SensorReadingService:
    """
    Encapsulates all business logic for SensorReading operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        sensor_reading_repository: SensorReadingRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._readings = sensor_reading_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_sensor_reading(
        self,
        field_id: uuid.UUID,
        payload: SensorReadingCreate,
    ) -> SensorReading:
        """
        Persist a new telemetry reading for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        InvalidSensorTimestampError
            If ``recorded_at`` is timezone-naive (ADR-007-25) or in the
            future (ADR-007-24).
        """
        log = logger.bind(
            field_id=str(field_id),
            sensor_type=payload.sensor_type.value,
        )

        # Rule 1 — parent field must exist (ADR-007-23)
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("sensor_reading_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rules 5 & 6 — timezone awareness and no future timestamps
        _validate_sensor_timestamp(recorded_at=payload.recorded_at, log=log)

        data: dict[str, Any] = {
            "field_id": field_id,
            **payload.model_dump(),
        }
        reading = await self._readings.create(data)
        log.info(
            "sensor_reading_service.create.success",
            sensor_reading_id=str(reading.id),
        )

        # ── Future extension point (ADR-007-26) ───────────────────────────────
        # This is the intended boundary for the following integrations.
        # Do NOT implement here; wire in a dedicated event-publishing adapter:
        #
        # - SensorReadingCreated event → Redpanda / Kafka topic
        # - Digital Twin field-state update
        # - CQRS read-model projection (e.g. latest reading per sensor_type)
        # - GaaS orchestration trigger
        # - Temporal workflow initiation (e.g. alert evaluation pipeline)
        # ─────────────────────────────────────────────────────────────────────

        return reading

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_sensor_reading(
        self,
        sensor_reading_id: uuid.UUID,
    ) -> SensorReading:
        """
        Return a single sensor reading by primary key.

        Raises
        ------
        SensorReadingNotFoundError
            If no reading with ``sensor_reading_id`` exists.
        """
        log = logger.bind(sensor_reading_id=str(sensor_reading_id))

        # Rule 2 — reading must exist
        reading = await self._readings.get_by_id(sensor_reading_id)
        if reading is None:
            log.warning("sensor_reading_service.get.not_found")
            raise SensorReadingNotFoundError(
                f"Sensor reading '{sensor_reading_id}' does not exist."
            )

        return reading

    async def list_field_sensor_readings(
        self,
        field_id: uuid.UUID,
    ) -> list[SensorReading]:
        """
        Return all sensor readings belonging to a field, ordered by
        recorded_at descending (most recent reading first).

        Repository ordering (``ORDER BY recorded_at DESC``) is authoritative;
        no reordering is applied in this layer.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists (rule 3).
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 3 — field must exist before listing its readings
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("sensor_reading_service.list.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        readings = await self._readings.list_by_field(field_id)
        log.debug(
            "sensor_reading_service.list.success",
            count=len(readings),
        )
        return readings

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_sensor_reading(
        self,
        sensor_reading_id: uuid.UUID,
    ) -> None:
        """
        Permanently remove a telemetry reading (administrative deletion).

        ``SensorReadingRepository.delete`` returns ``False`` when the record
        is absent, which satisfies rule 4 without requiring a separate
        existence query.

        Per ADR-007-28, deletion is permitted for administrative purposes
        (e.g. sensor calibration errors, data quality remediation).  This
        method must not be used for routine mutation of historical data.

        Raises
        ------
        SensorReadingNotFoundError
            If no reading with ``sensor_reading_id`` exists.
        """
        log = logger.bind(sensor_reading_id=str(sensor_reading_id))

        # Rule 4 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._readings.delete(sensor_reading_id)
        if not deleted:
            log.warning("sensor_reading_service.delete.not_found")
            raise SensorReadingNotFoundError(
                f"Sensor reading '{sensor_reading_id}' does not exist."
            )

        log.info("sensor_reading_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_sensor_timestamp(
    *,
    recorded_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidSensorTimestampError`` if ``recorded_at`` is timezone-naive
    or lies in the future.

    The timezone-awareness check (ADR-007-25) is applied first because a naive
    timestamp cannot be safely compared across UTC offsets.  Only after the
    timezone is confirmed valid is the future-timestamp check (ADR-007-24)
    performed.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    # ADR-007-25 — reject naive datetimes; IoT devices and ingestion gateways
    # must always supply an explicit UTC offset or 'Z' suffix.
    if recorded_at.tzinfo is None:
        log.warning(
            "sensor_reading_service.timestamp_naive",
            recorded_at=recorded_at.isoformat(),
        )
        raise InvalidSensorTimestampError(
            f"recorded_at ({recorded_at.isoformat()}) must be timezone-aware. "
            "Supply an ISO 8601 timestamp with an explicit UTC offset, "
            "e.g. 2026-06-18T20:00:00Z or 2026-06-18T22:00:00+02:00."
        )

    # ADR-007-24 — reject future timestamps; sensor readings represent past or
    # present physical observations, not forecasts or scheduled events.
    now_utc = datetime.now(timezone.utc)
    if recorded_at.astimezone(timezone.utc) > now_utc:
        log.warning(
            "sensor_reading_service.timestamp_future",
            recorded_at=recorded_at.isoformat(),
        )
        raise InvalidSensorTimestampError(
            f"recorded_at ({recorded_at.isoformat()}) cannot be in the future."
        )
