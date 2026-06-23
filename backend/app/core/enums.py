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


class IrrigationMethod(str, enum.Enum):
    """
    Delivery method used to apply water to a Field during an irrigation event.

    Inheriting ``str`` lets SQLAlchemy store the label as a plain VARCHAR,
    forward-compatible with schema changes and readable in raw SQL without a
    type cast.

    Method-specific application efficiency coefficients (used in FAO-56
    water balance models):
    - DRIP / SUBSURFACE  ~85–95 % distribution uniformity
    - SPRINKLER          ~70–85 %
    - CENTER_PIVOT       ~75–90 %
    - FURROW / FLOOD     ~50–70 %

    Used by:
    - IrrigationEvent  (Phase 8)
    - Digital Twin field water-balance state  (future)
    - Irrigation Optimization AI model        (future)
    - GaaS IrrigationAdvisor                 (future)
    """

    DRIP = "DRIP"
    SPRINKLER = "SPRINKLER"
    FLOOD = "FLOOD"
    FURROW = "FURROW"
    CENTER_PIVOT = "CENTER_PIVOT"
    SUBSURFACE = "SUBSURFACE"
    MANUAL = "MANUAL"
    AUTOMATED = "AUTOMATED"


class WaterSource(str, enum.Enum):
    """
    Origin of the water applied during an irrigation event.

    Used by:
    - IrrigationEvent  (Phase 8)
    - Water management analytics  (future)
    - Digital Twin resource allocation model  (future)
    """

    GROUNDWATER = "GROUNDWATER"
    SURFACE_WATER = "SURFACE_WATER"
    RAINWATER = "RAINWATER"
    MUNICIPAL = "MUNICIPAL"
    RECYCLED_WATER = "RECYCLED_WATER"


class YieldMeasurementMethod(str, enum.Enum):
    """
    Method used to obtain a yield measurement for a crop cycle.

    Placed in this shared module for cross-domain reuse across:
    - YieldRecord  (Phase 9)
    - Yield Prediction Engine  (Phase 12 — data quality weighting in training pipeline)
    - GaaS YieldAdvisor        (future — natural language yield history queries)
    - Digital Twin field productivity state  (future)

    Method-specific data quality notes:
    - COMBINE_MONITOR / YIELD_MAP  high spatial resolution; suitable for precision-ag
    - CROP_CUT                     FAO standard; statistically validated
    - LABORATORY_ANALYSIS          highest accuracy; low spatial coverage
    - REMOTE_SENSING               broad coverage; requires calibration against ground truth
    - MANUAL_SCALE                 reliable for small plots; labour-intensive at scale
    - ESTIMATED                    lowest confidence; for use when no instrument data exists
    """

    MANUAL_SCALE = "MANUAL_SCALE"
    COMBINE_MONITOR = "COMBINE_MONITOR"
    YIELD_MAP = "YIELD_MAP"
    REMOTE_SENSING = "REMOTE_SENSING"
    CROP_CUT = "CROP_CUT"
    LABORATORY_ANALYSIS = "LABORATORY_ANALYSIS"
    ESTIMATED = "ESTIMATED"


class DiseaseSeverity(str, enum.Enum):
    """
    Severity classification of a disease observation on a crop.

    Used by:
    - DiseaseObservation  (Phase 10)
    - Disease Risk Scoring Engine  (Phase 13 — label for model training)
    - GaaS PlantHealthAdvisor      (future — natural language risk queries)
    - Digital Twin crop health state  (future)

    Severity definitions:
    - LOW      minor symptoms; localised; no immediate yield threat
    - MEDIUM   moderate spread; intervention recommended
    - HIGH     significant disease pressure; yield loss expected
    - CRITICAL severe outbreak; urgent action required
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class DiagnosisMethod(str, enum.Enum):
    """
    Method by which a disease observation was identified or confirmed.

    Placed in this shared module for cross-domain reuse across:
    - DiseaseObservation  (Phase 10)
    - Disease Risk Scoring Engine  (Phase 13 — data quality weighting)
    - GaaS PlantHealthAdvisor      (future)
    - Digital Twin plant health state  (future)

    Method-specific confidence notes:
    - LAB_ANALYSIS      highest confidence; pathogen confirmed at species level
    - AGRONOMIST        high confidence; expert field assessment
    - IMAGE_AI          moderate confidence; depends on model accuracy and image quality
    - VISUAL_INSPECTION moderate confidence; farmer assessment without instruments
    - SENSOR_DETECTED   future capability; environmental threshold inference
    """

    VISUAL_INSPECTION = "VISUAL_INSPECTION"
    LAB_ANALYSIS = "LAB_ANALYSIS"
    IMAGE_AI = "IMAGE_AI"
    AGRONOMIST = "AGRONOMIST"
    SENSOR_DETECTED = "SENSOR_DETECTED"
