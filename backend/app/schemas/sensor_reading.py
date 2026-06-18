"""
Pydantic schemas for the SensorReading domain object.

Separation of concerns
----------------------
- SensorReadingBase     — shared field inventory; parent of SensorReadingResponse.
                          Defines the five telemetry measurement fields with their
                          validation rules so constraints are expressed exactly once.
- SensorReadingCreate   — inbound payload for POST
                          /fields/{field_id}/sensor-readings.
                          ``field_id`` is intentionally excluded; it is resolved
                          from the URL path by the router, matching the pattern
                          used by CropCreate, SoilProfileCreate, and
                          WeatherRecordCreate.  All four measurement fields are
                          required — a reading is meaningless without type, value,
                          unit, and timestamp.
- SensorReadingResponse — outbound representation returned to API consumers.
                          Extends SensorReadingBase with server-assigned identity
                          and audit fields.  ``from_attributes=True`` enables
                          direct construction from a SQLAlchemy ORM instance
                          without a manual mapping step.

Immutability contract
---------------------
SensorReading is append-only telemetry.  There is deliberately no
SensorReadingUpdate or PATCH endpoint.  Telemetry corrections are expressed as
new readings; the historical record is preserved intact.  This design is
forward-compatible with TimescaleDB hypertables, Cassandra immutable rows,
Redpanda event streaming, CQRS write models, and Digital Twin / GaaS topologies.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import SensorType


class SensorReadingBase(BaseModel):
    """
    Shared field inventory for the SensorReading domain.

    Inherited by SensorReadingResponse.  SensorReadingCreate mirrors these
    fields but is defined separately to follow the project convention — this
    also prevents accidental schema coupling if Create ever diverges from Base
    in future iterations (e.g. bulk ingestion payloads).
    """

    sensor_type: SensorType = Field(
        ...,
        description=(
            "Physical quantity measured by the sensor "
            "(SOIL_MOISTURE | SOIL_TEMPERATURE | AIR_TEMPERATURE | "
            "AIR_HUMIDITY | LIGHT_INTENSITY | LEAF_WETNESS | "
            "ELECTRICAL_CONDUCTIVITY | SOIL_SALINITY | WATER_LEVEL | "
            "BATTERY_STATUS | DEVICE_HEALTH)"
        ),
    )
    sensor_value: float = Field(
        ...,
        description=(
            "Raw numeric value recorded by the sensor.  Range is "
            "sensor_type-dependent and is not constrained here — validation "
            "of physical plausibility is the responsibility of the ingestion "
            "service (e.g. humidity must be in [0, 100])."
        ),
    )
    unit: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "SI or industry-standard unit for the recorded value "
            "(e.g. '%', '°C', 'lux', 'dS/m', 'mm', 'V')"
        ),
    )
    recorded_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when the sensor captured this reading "
            "(ISO 8601 with timezone offset, e.g. 2026-06-18T20:00:00+02:00). "
            "Must be supplied by the originating device or ingestion gateway; "
            "it is not generated server-side."
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Free-text annotations or anomaly flags from the ingestion pipeline",
    )


class SensorReadingCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/sensor-readings.

    ``field_id`` is excluded — it is injected from the URL path by the router.
    All four measurement fields (``sensor_type``, ``sensor_value``, ``unit``,
    ``recorded_at``) are required because a telemetry reading is meaningless
    without all of them.

    This schema intentionally has no defaults for measurement fields, enforcing
    that the ingestion client — not the API — is responsible for providing
    complete, accurate sensor data.
    """

    sensor_type: SensorType = Field(
        ...,
        description=(
            "Physical quantity measured by the sensor "
            "(SOIL_MOISTURE | SOIL_TEMPERATURE | AIR_TEMPERATURE | "
            "AIR_HUMIDITY | LIGHT_INTENSITY | LEAF_WETNESS | "
            "ELECTRICAL_CONDUCTIVITY | SOIL_SALINITY | WATER_LEVEL | "
            "BATTERY_STATUS | DEVICE_HEALTH)"
        ),
    )
    sensor_value: float = Field(
        ...,
        description=(
            "Raw numeric value recorded by the sensor.  Range is "
            "sensor_type-dependent; physical plausibility is validated "
            "by the ingestion service before this payload is accepted."
        ),
    )
    unit: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description=(
            "SI or industry-standard unit for the recorded value "
            "(e.g. '%', '°C', 'lux', 'dS/m', 'mm', 'V')"
        ),
    )
    recorded_at: datetime = Field(
        ...,
        description=(
            "Timezone-aware timestamp when the sensor captured this reading "
            "(ISO 8601 with timezone offset, e.g. 2026-06-18T20:00:00+02:00)"
        ),
    )
    notes: str | None = Field(
        default=None,
        description="Free-text annotations or anomaly flags from the ingestion pipeline",
    )


class SensorReadingResponse(SensorReadingBase):
    """
    Outbound representation of a SensorReading returned to API consumers.

    Extends SensorReadingBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.

    ``updated_at`` is included for API consistency with other domain responses.
    For append-only readings it will always equal ``created_at`` — this is
    a deliberate design signal that the record has never been mutated.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the sensor reading")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
