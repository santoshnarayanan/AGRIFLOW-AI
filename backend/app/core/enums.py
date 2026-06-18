"""
Shared domain enumerations for AGRIFLOW-AI.

All enums in this module are designed for cross-domain reuse.  Placing them
here prevents circular imports between ORM models, schemas, services, and
future domains such as SensorDevice, SensorAlert, Telemetry Ingestion,
Digital Twin, and the AI Recommendation Engine.

Convention:
- Every enum inherits from ``str`` so SQLAlchemy stores the label as a plain
  VARCHAR — forward-compatible with schema changes and readable in raw SQL
  without requiring a type cast.
- Enum ``name`` kwargs passed to SQLAlchemy ``Enum(...)`` are kept in
  snake_case and match the column name in the database (e.g. "sensor_type").
"""

import enum


class SensorType(str, enum.Enum):
    """
    Discriminator for the physical quantity an IoT sensor measures.

    Used by:
    - SensorReading  (telemetry readings attached to a Field)
    - SensorDevice   (future — device registry and calibration)
    - SensorAlert    (future — threshold-based alert rules)
    - Telemetry Ingestion pipeline
    - Digital Twin topology
    - AI Recommendation Engine
    """

    SOIL_MOISTURE = "SOIL_MOISTURE"
    SOIL_TEMPERATURE = "SOIL_TEMPERATURE"
    AIR_TEMPERATURE = "AIR_TEMPERATURE"
    AIR_HUMIDITY = "AIR_HUMIDITY"
    LIGHT_INTENSITY = "LIGHT_INTENSITY"
    LEAF_WETNESS = "LEAF_WETNESS"
    ELECTRICAL_CONDUCTIVITY = "ELECTRICAL_CONDUCTIVITY"
    SOIL_SALINITY = "SOIL_SALINITY"
    WATER_LEVEL = "WATER_LEVEL"
    BATTERY_STATUS = "BATTERY_STATUS"
    DEVICE_HEALTH = "DEVICE_HEALTH"
