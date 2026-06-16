"""
WeatherRecordService — business logic for the WeatherRecord domain.

Responsibilities
----------------
- Verify the parent field exists before creating a weather record.   (rule 1)
- Verify a weather record exists before applying an update.          (rule 2)
- Verify a weather record exists before deletion.                    (rule 3)
- Ensure recorded_at is not in the future.                           (rule 4)
- Ensure humidity_percent is within the range [0, 100].              (rule 5)
- Ensure rainfall_mm is non-negative.                                (rule 6)
- Ensure wind_speed_kmh is non-negative.                             (rule 7)
- Ensure solar_radiation_wm2 is non-negative when provided.         (rule 8)
- Ensure temperature_max_c >= temperature_min_c when both provided. (rule 9)

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.weather_record import WeatherRecord
from app.db.repositories.field import FieldRepository
from app.db.repositories.weather_record import WeatherRecordRepository
from app.schemas.weather_record import WeatherRecordCreate, WeatherRecordUpdate
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class WeatherRecordNotFoundError(ValueError):
    """Raised when the referenced weather record does not exist."""


class InvalidWeatherTimestampError(ValueError):
    """
    Raised when ``recorded_at`` is set to a future timestamp.

    Weather observations must represent past or present readings.  Allowing
    future timestamps would corrupt time-series ordering and produce misleading
    agronomic analytics.  This invariant is enforced here at the service layer
    rather than in the database so that callers receive a meaningful error
    message rather than a constraint violation.
    """


class InvalidWeatherMeasurementError(ValueError):
    """
    Raised when a measurement value violates a physical domain constraint.

    Enforced constraints:
    - ``humidity_percent`` must be in the range [0.00, 100.00].
    - ``rainfall_mm`` must be non-negative.
    - ``wind_speed_kmh`` must be non-negative.
    - ``solar_radiation_wm2`` must be non-negative.

    These constraints are also expressed in the Pydantic schema layer; the
    service layer re-validates them to remain independent of the transport
    mechanism and to provide defence-in-depth for programmatic callers.
    """


class InvalidTemperatureRangeError(ValueError):
    """
    Raised when temperature_max_c is less than temperature_min_c.

    A daily maximum temperature below the minimum is physically impossible and
    would corrupt Growing Degree Day (GDD) calculations. This invariant is
    enforced only when both values are present in the same payload — a partial
    update supplying only one of the two fields does not trigger this check.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class WeatherRecordService:
    """
    Encapsulates all business logic for WeatherRecord operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        weather_record_repository: WeatherRecordRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._records = weather_record_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_weather_record(
        self,
        field_id: uuid.UUID,
        payload: WeatherRecordCreate,
    ) -> WeatherRecord:
        """
        Persist a new weather observation for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        InvalidWeatherTimestampError
            If ``recorded_at`` is in the future.
        InvalidWeatherMeasurementError
            If ``humidity_percent``, ``rainfall_mm``, ``wind_speed_kmh``, or
            ``solar_radiation_wm2`` violate their domain constraints.
        InvalidTemperatureRangeError
            If ``temperature_max_c`` is less than ``temperature_min_c``.
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("weather_record_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 4 — recorded_at must not be in the future
        _validate_timestamp(recorded_at=payload.recorded_at, log=log)

        # Rules 5, 6, 7 — measurement bounds
        _validate_measurements(
            humidity_percent=payload.humidity_percent,
            rainfall_mm=payload.rainfall_mm,
            wind_speed_kmh=payload.wind_speed_kmh,
            solar_radiation_wm2=payload.solar_radiation_wm2,
            log=log,
        )

        # Rule 8 — temperature_max_c must not be less than temperature_min_c
        _validate_temperature_range(
            temperature_min_c=payload.temperature_min_c,
            temperature_max_c=payload.temperature_max_c,
            log=log,
        )

        data: dict[str, Any] = {
            "field_id": field_id,
            **payload.model_dump(),
        }
        record = await self._records.create(data)
        log.info("weather_record_service.create.success", record_id=str(record.id))
        return record

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_weather_record(
        self,
        weather_record_id: uuid.UUID,
    ) -> WeatherRecord | None:
        """
        Return a single weather record by primary key.

        Returns ``None`` when no record with ``weather_record_id`` exists so
        that callers can decide whether a missing resource is an error
        (e.g. raise HTTP 404).
        """
        record = await self._records.get_by_id(weather_record_id)
        if record is None:
            logger.bind(record_id=str(weather_record_id)).debug(
                "weather_record_service.get.not_found"
            )
        return record

    async def list_field_weather_records(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[WeatherRecord]:
        """
        Return all weather observations belonging to a field, ordered by
        recorded_at descending (most recent observation first).

        An empty list is returned when the field has no records or does not
        exist; field validation at list-time is the responsibility of the
        caller when required.
        """
        return await self._records.list_by_field(
            field_id,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_weather_record(
        self,
        weather_record_id: uuid.UUID,
        payload: WeatherRecordUpdate,
    ) -> WeatherRecord:
        """
        Apply a partial update to an existing weather record.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.  Validation is applied to each incoming value
        independently — it is not necessary to load the stored values for
        these stateless physical-domain checks.

        Raises
        ------
        WeatherRecordNotFoundError
            If no weather record with ``weather_record_id`` exists.
        InvalidWeatherTimestampError
            If the supplied ``recorded_at`` is in the future.
        InvalidWeatherMeasurementError
            If any supplied measurement value violates its domain constraint.
        """
        log = logger.bind(record_id=str(weather_record_id))

        # Rule 2 — record must exist before update
        current = await self._records.get_by_id(weather_record_id)
        if current is None:
            log.warning("weather_record_service.update.not_found")
            raise WeatherRecordNotFoundError(
                f"Weather record '{weather_record_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 4 — validate timestamp only if the caller is changing it
        if "recorded_at" in update_data:
            _validate_timestamp(recorded_at=update_data["recorded_at"], log=log)

        # Rules 5, 6, 7 — validate measurements only for the fields being updated;
        # None is passed for fields absent from the payload and is treated as
        # "no change" by the helper (no validation performed for those fields).
        _validate_measurements(
            humidity_percent=update_data.get("humidity_percent"),
            rainfall_mm=update_data.get("rainfall_mm"),
            wind_speed_kmh=update_data.get("wind_speed_kmh"),
            solar_radiation_wm2=update_data.get("solar_radiation_wm2"),
            log=log,
        )

        # Rule 8 — validate temperature range only when both extremes are
        # present after applying the update. Resolve effective values the same
        # way as rule 4: incoming value takes priority over the stored value.
        _validate_temperature_range(
            temperature_min_c=update_data.get("temperature_min_c", current.temperature_min_c),
            temperature_max_c=update_data.get("temperature_max_c", current.temperature_max_c),
            log=log,
        )

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._records.update(weather_record_id, update_data)
        log.info("weather_record_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_weather_record(self, weather_record_id: uuid.UUID) -> None:
        """
        Permanently remove a weather record.

        ``WeatherRecordRepository.delete`` returns ``False`` when the record is
        absent, which satisfies rule 3 without requiring a separate existence
        query.

        Raises
        ------
        WeatherRecordNotFoundError
            If no weather record with ``weather_record_id`` exists.
        """
        log = logger.bind(record_id=str(weather_record_id))

        # Rule 3 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._records.delete(weather_record_id)
        if not deleted:
            log.warning("weather_record_service.delete.not_found")
            raise WeatherRecordNotFoundError(
                f"Weather record '{weather_record_id}' does not exist."
            )

        log.info("weather_record_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_timestamp(
    *,
    recorded_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidWeatherTimestampError`` if ``recorded_at`` is in the future.

    The comparison is performed in UTC regardless of the incoming timezone so
    that observations from fields in non-UTC offsets are evaluated correctly.
    A timezone-naive ``recorded_at`` is treated as UTC (matching PostgreSQL
    behaviour when storing into a TIMESTAMPTZ column).

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    now_utc = datetime.now(timezone.utc)
    recorded_at_utc = (
        recorded_at.replace(tzinfo=timezone.utc)
        if recorded_at.tzinfo is None
        else recorded_at.astimezone(timezone.utc)
    )
    if recorded_at_utc > now_utc:
        log.warning(
            "weather_record_service.timestamp_invalid",
            recorded_at=recorded_at.isoformat(),
        )
        raise InvalidWeatherTimestampError(
            f"recorded_at ({recorded_at.isoformat()}) cannot be in the future."
        )


def _validate_measurements(
    *,
    humidity_percent: Decimal | None,
    rainfall_mm: Decimal | None,
    wind_speed_kmh: Decimal | None,
    solar_radiation_wm2: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidWeatherMeasurementError`` for any out-of-range measurement.

    Each parameter is optional (``None`` means "not being set / not changed");
    only the values that are explicitly provided are validated.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if humidity_percent is not None and not (
        Decimal("0") <= humidity_percent <= Decimal("100")
    ):
        log.warning(
            "weather_record_service.humidity_invalid",
            humidity_percent=str(humidity_percent),
        )
        raise InvalidWeatherMeasurementError(
            f"humidity_percent ({humidity_percent}) must be in the range [0, 100]."
        )

    if rainfall_mm is not None and rainfall_mm < Decimal("0"):
        log.warning(
            "weather_record_service.rainfall_invalid",
            rainfall_mm=str(rainfall_mm),
        )
        raise InvalidWeatherMeasurementError(
            f"rainfall_mm ({rainfall_mm}) must be non-negative."
        )

    if wind_speed_kmh is not None and wind_speed_kmh < Decimal("0"):
        log.warning(
            "weather_record_service.wind_speed_invalid",
            wind_speed_kmh=str(wind_speed_kmh),
        )
        raise InvalidWeatherMeasurementError(
            f"wind_speed_kmh ({wind_speed_kmh}) must be non-negative."
        )

    if solar_radiation_wm2 is not None and solar_radiation_wm2 < Decimal("0"):
        log.warning(
            "weather_record_service.solar_radiation_invalid",
            solar_radiation_wm2=str(solar_radiation_wm2),
        )
        raise InvalidWeatherMeasurementError(
            f"solar_radiation_wm2 ({solar_radiation_wm2}) must be non-negative."
        )


def _validate_temperature_range(
    *,
    temperature_min_c: Decimal | None,
    temperature_max_c: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidTemperatureRangeError`` when temperature_max_c < temperature_min_c.

    The check is only applied when both values are present — a partial payload
    supplying only one extreme is valid (the other remains at its stored value
    and the stored pair was already validated on a prior write).

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if (
        temperature_min_c is not None
        and temperature_max_c is not None
        and temperature_max_c < temperature_min_c
    ):
        log.warning(
            "weather_record_service.temperature_range_invalid",
            temperature_min_c=str(temperature_min_c),
            temperature_max_c=str(temperature_max_c),
        )
        raise InvalidTemperatureRangeError(
            f"temperature_max_c ({temperature_max_c}) must be greater than or equal to "
            f"temperature_min_c ({temperature_min_c})."
        )
