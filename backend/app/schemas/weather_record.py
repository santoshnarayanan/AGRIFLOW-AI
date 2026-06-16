"""
Pydantic schemas for the WeatherRecord domain object.

Separation of concerns
----------------------
- WeatherRecordBase     — shared field inventory; parent of WeatherRecordResponse.
                          Defines all six weather measurement fields with their
                          validation rules so constraints are expressed exactly once.
- WeatherRecordCreate   — inbound payload for POST /fields/{field_id}/weather-records.
                          ``field_id`` is intentionally excluded; it is resolved from
                          the URL path by the router, matching the pattern used by
                          CropCreate and SoilProfileCreate.  ``rainfall_mm``,
                          ``wind_speed_kmh``, and ``data_source`` carry sensible
                          defaults that mirror the database server_default values.
- WeatherRecordUpdate   — inbound payload for PATCH
                          /fields/{field_id}/weather-records/{record_id}.
                          Every field is optional to support sparse partial updates.
                          All validation constraints from WeatherRecordCreate are
                          retained so a partial payload is never weaker than a full one.
- WeatherRecordResponse — outbound representation returned to API consumers.
                          Extends WeatherRecordBase with server-assigned identity and
                          audit fields.  ``from_attributes=True`` enables direct
                          construction from a SQLAlchemy ORM instance.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class WeatherRecordBase(BaseModel):
    """
    Shared field inventory for the WeatherRecord domain.

    Inherited by WeatherRecordResponse.  WeatherRecordCreate and
    WeatherRecordUpdate mirror these fields but are defined separately to
    follow the project convention — this also prevents accidental schema
    coupling when Create/Update diverge from the Base in future iterations.
    """

    recorded_at: datetime = Field(
        ...,
        description=(
            "Timestamp when the weather observation was recorded "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T09:00:00+02:00)"
        ),
    )
    temperature_c: Decimal = Field(
        ...,
        decimal_places=2,
        description="Air temperature in degrees Celsius; sub-zero values are valid",
    )
    humidity_percent: Decimal = Field(
        ...,
        ge=0,
        le=100,
        decimal_places=2,
        description="Relative humidity as a percentage — range [0.00, 100.00]",
    )
    rainfall_mm: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Cumulative rainfall in millimeters; must be non-negative",
    )
    wind_speed_kmh: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Wind speed in kilometers per hour; must be non-negative",
    )
    data_source: str = Field(
        default="MANUAL",
        max_length=50,
        description=(
            "Origin of the weather data "
            "(e.g. MANUAL, IOT_SENSOR, WEATHER_API)"
        ),
    )

    # ── Solar / temperature range (P1 — Yield Prediction) ────────────────────
    # Note: temperature_c retains its existing semantics (current/point-in-time
    # reading). temperature_min_c and temperature_max_c represent the daily
    # extremes required for Growing Degree Day (GDD) accumulation calculations.
    solar_radiation_wm2: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Solar irradiance in W/m²; required for Penman-Monteith ET₀ calculation",
    )
    temperature_min_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily minimum air temperature in °C; used for GDD calculation",
    )
    temperature_max_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily maximum air temperature in °C; used for GDD calculation",
    )


class WeatherRecordCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/weather-records.

    ``field_id`` is excluded — it is injected from the URL path by the router.
    ``recorded_at``, ``temperature_c``, and ``humidity_percent`` are required
    because they represent the core observation.  ``rainfall_mm``,
    ``wind_speed_kmh``, and ``data_source`` default to values that match the
    database server_default so callers can omit them for sensor types that do
    not measure every metric.
    """

    recorded_at: datetime = Field(
        ...,
        description=(
            "Timestamp when the weather observation was recorded "
            "(ISO 8601 with timezone offset, e.g. 2026-06-15T09:00:00+02:00)"
        ),
    )
    temperature_c: Decimal = Field(
        ...,
        decimal_places=2,
        description="Air temperature in degrees Celsius; sub-zero values are valid",
    )
    humidity_percent: Decimal = Field(
        ...,
        ge=0,
        le=100,
        decimal_places=2,
        description="Relative humidity as a percentage — range [0.00, 100.00]",
    )
    rainfall_mm: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Cumulative rainfall in millimeters; must be non-negative",
    )
    wind_speed_kmh: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        decimal_places=2,
        description="Wind speed in kilometers per hour; must be non-negative",
    )
    data_source: str = Field(
        default="MANUAL",
        max_length=50,
        description=(
            "Origin of the weather data "
            "(e.g. MANUAL, IOT_SENSOR, WEATHER_API)"
        ),
    )

    # ── Solar / temperature range (P1 — Yield Prediction) ────────────────────
    solar_radiation_wm2: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Solar irradiance in W/m²; required for Penman-Monteith ET₀ calculation",
    )
    temperature_min_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily minimum air temperature in °C; used for GDD calculation",
    )
    temperature_max_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily maximum air temperature in °C; used for GDD calculation",
    )


class WeatherRecordUpdate(BaseModel):
    """
    Request body for PATCH /fields/{field_id}/weather-records/{record_id}.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller.  All
    validation constraints match WeatherRecordCreate so a partial payload
    is never weaker than a full one.
    """

    recorded_at: datetime | None = Field(
        default=None,
        description=(
            "Timestamp when the weather observation was recorded "
            "(ISO 8601 with timezone offset)"
        ),
    )
    temperature_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Air temperature in degrees Celsius; sub-zero values are valid",
    )
    humidity_percent: Decimal | None = Field(
        default=None,
        ge=0,
        le=100,
        decimal_places=2,
        description="Relative humidity as a percentage — range [0.00, 100.00]",
    )
    rainfall_mm: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Cumulative rainfall in millimeters; must be non-negative",
    )
    wind_speed_kmh: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Wind speed in kilometers per hour; must be non-negative",
    )
    data_source: str | None = Field(
        default=None,
        max_length=50,
        description="Origin of the weather data",
    )

    # ── Solar / temperature range (P1 — Yield Prediction) ────────────────────
    solar_radiation_wm2: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Solar irradiance in W/m²",
    )
    temperature_min_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily minimum air temperature in °C",
    )
    temperature_max_c: Decimal | None = Field(
        default=None,
        decimal_places=2,
        description="Daily maximum air temperature in °C",
    )


class WeatherRecordResponse(WeatherRecordBase):
    """
    Outbound representation of a WeatherRecord returned to API consumers.

    Extends WeatherRecordBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the weather record")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
