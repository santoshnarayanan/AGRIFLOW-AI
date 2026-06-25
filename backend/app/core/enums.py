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


class SatelliteProvider(str, enum.Enum):
    """
    Satellite platform or data provider that sourced the imagery for an
    observation.

    Placed in this shared module for cross-domain reuse across:
    - SatelliteObservation  (Phase 11)
    - AI Prediction Engines  (Phase 12–13 — training data provenance and
      spatial-resolution weighting)
    - Digital Twin field state  (future — imagery ingestion pipeline)
    - GaaS SatelliteAdvisor    (future — natural language crop health queries)

    Provider-specific characteristics relevant to AI data quality weighting:
    - SENTINEL_2   ESA Copernicus; 10 m multispectral; 5-day revisit; free
    - LANDSAT_8    USGS/NASA;      30 m multispectral; 16-day revisit; free
    - LANDSAT_9    USGS/NASA;      30 m multispectral; 16-day revisit; free
    - PLANET       Planet Labs;    3–5 m multispectral; daily revisit; commercial
    - MODIS        NASA;           250 m–1 km; daily revisit; free; broad coverage
    - SPOT         Airbus;         1.5–6 m; commercial
    - WORLDVIEW    Maxar;          0.3–1.2 m very high resolution; commercial
    - UNKNOWN      Provider not recorded or data ingested without provenance
    """

    SENTINEL_2 = "SENTINEL_2"
    LANDSAT_8 = "LANDSAT_8"
    LANDSAT_9 = "LANDSAT_9"
    PLANET = "PLANET"
    MODIS = "MODIS"
    SPOT = "SPOT"
    WORLDVIEW = "WORLDVIEW"
    UNKNOWN = "UNKNOWN"


class SpectralIndex(str, enum.Enum):
    """
    Derived spectral or vegetation index computed from satellite band
    reflectance values.

    Placed in this shared module for cross-domain reuse across:
    - SatelliteObservation  (Phase 11 — primary measurement discriminator)
    - Yield Prediction Engine  (Phase 12 — NDVI/EVI as growing-season feature)
    - Disease Risk Engine       (Phase 13 — NDRE/NDVI as early-stress signal)
    - Irrigation Recommendation Engine  (Phase 14 — NDWI for water-stress detection)
    - Digital Twin crop state   (future — vegetation health time-series)
    - GaaS SatelliteAdvisor     (future — index-specific natural language queries)

    Index-specific agricultural interpretation:
    - NDVI   Normalized Difference Vegetation Index; general canopy greenness
             and biomass; range [-1, 1]; most widely used vegetation index
    - EVI    Enhanced Vegetation Index; corrects for atmospheric and canopy
             background effects; better performance in high-biomass areas
    - NDWI   Normalized Difference Water Index; crop water content and stress;
             sensitive to leaf water content changes before visible wilting
    - SAVI   Soil-Adjusted Vegetation Index; NDVI variant for sparse vegetation
             where soil background reflectance distorts the signal
    - NDRE   Normalized Difference Red Edge; early detection of crop stress and
             nitrogen deficiency before visible chlorophyll degradation
    - LAI    Leaf Area Index; total one-sided leaf area per unit ground area;
             structural canopy measure used in crop growth models
    - MSAVI  Modified Soil-Adjusted Vegetation Index; improved SAVI reducing
             soil noise without requiring an empirical soil factor
    - GNDVI  Green Normalized Difference Vegetation Index; green band variant;
             more sensitive to chlorophyll concentration than NDVI
    """

    NDVI = "NDVI"
    EVI = "EVI"
    NDWI = "NDWI"
    SAVI = "SAVI"
    NDRE = "NDRE"
    LAI = "LAI"
    MSAVI = "MSAVI"
    GNDVI = "GNDVI"


class ProcessingLevel(str, enum.Enum):
    """
    Processing tier applied to the raw satellite data before the spectral
    index was computed.

    Placed in this shared module for cross-domain reuse across:
    - SatelliteObservation  (Phase 11 — data quality provenance)
    - AI Prediction Engines  (Phase 12–14 — training data quality weighting;
      ARD and L2A observations are preferred inputs)
    - Satellite ingestion pipeline  (future — ETL validation gate)
    - Digital Twin field state      (future — imagery quality filter)

    Level-specific data quality and reproducibility notes:
    - L1C      Top-of-atmosphere (TOA) reflectance; not atmospherically corrected;
               lowest comparability across dates and sensors
    - L2A      Bottom-of-atmosphere (BOA) surface reflectance; atmospherically
               corrected; the standard input for most index computation pipelines
    - ARD      Analysis-Ready Data; L2A with additional cloud masking, geometric
               correction, and normalisation applied; highest reproducibility
    - DERIVED  Post-processed composite or mosaic product (e.g. seasonal mean,
               gap-filled time-series); suitable for trend analysis but not
               single-date phenology extraction
    """

    L1C = "L1C"
    L2A = "L2A"
    ARD = "ARD"
    DERIVED = "DERIVED"
