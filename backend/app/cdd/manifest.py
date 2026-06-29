"""
CDD manifest — single source of truth for all configurable dataset parameters.

No generation logic lives here. Factories and the orchestrator read manifest values
rather than embedding hard-coded counts, cadences, or domain rules.

Profile extensibility: register new profiles via ``register_profile()`` without
modifying factories or the orchestrator. See ``FUTURE_PROFILES`` for planned profiles.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core.enums import (
    DiagnosisMethod,
    DiseaseSeverity,
    IrrigationMethod,
    SensorType,
    WaterSource,
    YieldMeasurementMethod,
)
from app.cdd.config import DEFAULT_PROFILE


@dataclass(frozen=True, slots=True)
class SeasonPhase:
    """Named agricultural season window expressed as day offsets from temporal start."""

    name: str
    start_day: int
    end_day: int


@dataclass(frozen=True, slots=True)
class FieldDefinition:
    """Static field portfolio entry for the AGRIFLOW Demonstration Farm."""

    field_code: str
    name: str
    area_hectares: float
    soil_texture_label: str
    irrigation_method: IrrigationMethod | None
    is_irrigated: bool
    elevation_m: float
    latitude_offset: float
    longitude_offset: float
    soil_moisture_threshold_pct: float
    water_source: WaterSource | None


@dataclass(frozen=True, slots=True)
class CropRotationEntry:
    """Planned crop cycle within the 365-day horizon."""

    field_code: str
    crop_name: str
    crop_variety: str | None
    planting_date: date
    expected_harvest_date: date
    is_perennial: bool
    expected_yield_tons_ha: float
    seeding_rate_kg_ha: float | None
    is_susceptible_to_disease: bool
    primary_disease: str | None = None


@dataclass(frozen=True, slots=True)
class SensorCadenceConfig:
    """Sensor measurement frequency and deployed types."""

    frequency_hours: int
    sensor_types: tuple[SensorType, ...]


@dataclass(frozen=True, slots=True)
class WeatherCadenceConfig:
    """Weather observation schedule."""

    observations_per_day: int
    hours_between_observations: int


@dataclass(frozen=True, slots=True)
class SatelliteCadenceConfig:
    """Satellite revisit and index coverage."""

    revisit_days: int
    spectral_indices: tuple[str, ...]
    primary_provider: str
    supplementary_provider: str
    processing_level: str
    resolution_m: float


@dataclass(frozen=True, slots=True)
class DiseaseFrequencyConfig:
    """Disease observation density per crop cycle."""

    observations_per_crop: int
    severity_distribution: tuple[tuple[DiseaseSeverity, float], ...]
    diagnosis_methods: tuple[DiagnosisMethod, ...]


@dataclass(frozen=True, slots=True)
class IrrigationRulesConfig:
    """Soil-moisture-driven irrigation trigger rules."""

    season_start_month: int
    season_end_month: int
    deficit_hours_required: int
    events_per_irrigated_field_min: int
    events_per_irrigated_field_max: int
    default_water_volume_liters: float
    default_duration_minutes: float


@dataclass(frozen=True, slots=True)
class YieldRulesConfig:
    """Harvest yield measurement rules."""

    measurement_methods: tuple[YieldMeasurementMethod, ...]
    records_per_annual_crop: int
    records_per_perennial_crop: int


@dataclass(frozen=True, slots=True)
class FarmDefinition:
    """Root farm identity for the demonstration dataset."""

    farm_code: str
    farm_name: str
    owner_name: str
    country: str
    state: str
    city: str
    latitude: float
    longitude: float
    timezone: str


@dataclass(frozen=True, slots=True)
class CDDManifest:
    """Complete manifest for a named scale profile."""

    profile_name: str
    farm_count: int
    field_count: int
    temporal_duration_days: int
    farm: FarmDefinition
    fields: tuple[FieldDefinition, ...]
    crop_rotations: tuple[CropRotationEntry, ...]
    sensor: SensorCadenceConfig
    weather: WeatherCadenceConfig
    satellite: SatelliteCadenceConfig
    disease: DiseaseFrequencyConfig
    irrigation: IrrigationRulesConfig
    yield_rules: YieldRulesConfig
    season_phases: tuple[SeasonPhase, ...]
    target_row_counts: dict[str, int]


# ── Season phases (day offsets from TEMPORAL_START) ─────────────────────────
_SEASON_PHASES: tuple[SeasonPhase, ...] = (
    SeasonPhase("dormancy", 1, 60),
    SeasonPhase("dormancy_late", 330, 365),
    SeasonPhase("planting", 61, 90),
    SeasonPhase("early_growth", 91, 150),
    SeasonPhase("peak_growing", 151, 240),
    SeasonPhase("reproductive", 241, 280),
    SeasonPhase("harvest", 281, 310),
    SeasonPhase("post_harvest", 311, 329),
)

# ── Field portfolio (AGRIFLOW Demonstration Farm) ─────────────────────────────
_FIELD_PORTFOLIO: tuple[FieldDefinition, ...] = (
    FieldDefinition(
        field_code="F01",
        name="North Wheat Pivot",
        area_hectares=45.0,
        soil_texture_label="Loam",
        irrigation_method=IrrigationMethod.CENTER_PIVOT,
        is_irrigated=True,
        elevation_m=312.0,
        latitude_offset=0.012,
        longitude_offset=-0.008,
        soil_moisture_threshold_pct=28.0,
        water_source=WaterSource.GROUNDWATER,
    ),
    FieldDefinition(
        field_code="F02",
        name="South Corn Block",
        area_hectares=38.0,
        soil_texture_label="Clay Loam",
        irrigation_method=IrrigationMethod.SPRINKLER,
        is_irrigated=True,
        elevation_m=298.0,
        latitude_offset=-0.015,
        longitude_offset=0.005,
        soil_moisture_threshold_pct=30.0,
        water_source=WaterSource.SURFACE_WATER,
    ),
    FieldDefinition(
        field_code="F03",
        name="East Soy Belt",
        area_hectares=52.0,
        soil_texture_label="Silt Loam",
        irrigation_method=None,
        is_irrigated=False,
        elevation_m=285.0,
        latitude_offset=0.020,
        longitude_offset=0.018,
        soil_moisture_threshold_pct=25.0,
        water_source=None,
    ),
    FieldDefinition(
        field_code="F04",
        name="West Mixed Rotation",
        area_hectares=41.0,
        soil_texture_label="Sandy Loam",
        irrigation_method=IrrigationMethod.DRIP,
        is_irrigated=True,
        elevation_m=305.0,
        latitude_offset=-0.010,
        longitude_offset=-0.022,
        soil_moisture_threshold_pct=26.0,
        water_source=WaterSource.GROUNDWATER,
    ),
    FieldDefinition(
        field_code="F05",
        name="River Bottom Alfalfa",
        area_hectares=28.0,
        soil_texture_label="Silty Clay",
        irrigation_method=IrrigationMethod.FLOOD,
        is_irrigated=True,
        elevation_m=268.0,
        latitude_offset=0.005,
        longitude_offset=-0.003,
        soil_moisture_threshold_pct=32.0,
        water_source=WaterSource.SURFACE_WATER,
    ),
    FieldDefinition(
        field_code="F06",
        name="Hilltop Barley",
        area_hectares=22.0,
        soil_texture_label="Loam",
        irrigation_method=None,
        is_irrigated=False,
        elevation_m=342.0,
        latitude_offset=0.008,
        longitude_offset=0.012,
        soil_moisture_threshold_pct=24.0,
        water_source=None,
    ),
    FieldDefinition(
        field_code="F07",
        name="Valley Potato",
        area_hectares=18.0,
        soil_texture_label="Sandy",
        irrigation_method=IrrigationMethod.DRIP,
        is_irrigated=True,
        elevation_m=276.0,
        latitude_offset=-0.006,
        longitude_offset=0.009,
        soil_moisture_threshold_pct=35.0,
        water_source=WaterSource.MUNICIPAL,
    ),
    FieldDefinition(
        field_code="F08",
        name="Orchard Edge",
        area_hectares=15.0,
        soil_texture_label="Loam",
        irrigation_method=IrrigationMethod.SUBSURFACE,
        is_irrigated=True,
        elevation_m=318.0,
        latitude_offset=0.003,
        longitude_offset=-0.014,
        soil_moisture_threshold_pct=29.0,
        water_source=WaterSource.RECYCLED_WATER,
    ),
    FieldDefinition(
        field_code="F09",
        name="Research Plot A",
        area_hectares=8.0,
        soil_texture_label="Clay",
        irrigation_method=IrrigationMethod.MANUAL,
        is_irrigated=True,
        elevation_m=301.0,
        latitude_offset=-0.002,
        longitude_offset=0.006,
        soil_moisture_threshold_pct=31.0,
        water_source=WaterSource.GROUNDWATER,
    ),
    FieldDefinition(
        field_code="F10",
        name="Research Plot B",
        area_hectares=8.0,
        soil_texture_label="Loam",
        irrigation_method=IrrigationMethod.AUTOMATED,
        is_irrigated=True,
        elevation_m=299.0,
        latitude_offset=0.001,
        longitude_offset=-0.001,
        soil_moisture_threshold_pct=27.0,
        water_source=WaterSource.GROUNDWATER,
    ),
)

# ── Crop rotations (18 records across two partial growing seasons) ─────────────
_CROP_ROTATIONS: tuple[CropRotationEntry, ...] = (
    CropRotationEntry(
        field_code="F01",
        crop_name="Winter Wheat",
        crop_variety="SY Viper",
        planting_date=date(2025, 6, 15),
        expected_harvest_date=date(2026, 3, 20),
        is_perennial=False,
        expected_yield_tons_ha=6.8,
        seeding_rate_kg_ha=120.0,
        is_susceptible_to_disease=True,
        primary_disease="Stripe Rust",
    ),
    CropRotationEntry(
        field_code="F01",
        crop_name="Soybean",
        crop_variety="P31A22X",
        planting_date=date(2026, 4, 25),
        expected_harvest_date=date(2026, 5, 28),
        is_perennial=False,
        expected_yield_tons_ha=3.2,
        seeding_rate_kg_ha=75.0,
        is_susceptible_to_disease=True,
        primary_disease="Frogeye Leaf Spot",
    ),
    CropRotationEntry(
        field_code="F02",
        crop_name="Corn",
        crop_variety="DKC 6870",
        planting_date=date(2025, 8, 10),
        expected_harvest_date=date(2026, 3, 15),
        is_perennial=False,
        expected_yield_tons_ha=11.5,
        seeding_rate_kg_ha=32.0,
        is_susceptible_to_disease=True,
        primary_disease="Gray Leaf Spot",
    ),
    CropRotationEntry(
        field_code="F02",
        crop_name="Winter Wheat",
        crop_variety="SY Viper",
        planting_date=date(2026, 5, 18),
        expected_harvest_date=date(2026, 5, 31),
        is_perennial=False,
        expected_yield_tons_ha=2.1,
        seeding_rate_kg_ha=110.0,
        is_susceptible_to_disease=False,
    ),
    CropRotationEntry(
        field_code="F03",
        crop_name="Soybean",
        crop_variety="AG47X7",
        planting_date=date(2025, 8, 5),
        expected_harvest_date=date(2026, 3, 10),
        is_perennial=False,
        expected_yield_tons_ha=3.8,
        seeding_rate_kg_ha=70.0,
        is_susceptible_to_disease=True,
        primary_disease="Sudden Death Syndrome",
    ),
    CropRotationEntry(
        field_code="F03",
        crop_name="Corn",
        crop_variety="P1197AM",
        planting_date=date(2026, 4, 20),
        expected_harvest_date=date(2026, 5, 25),
        is_perennial=False,
        expected_yield_tons_ha=4.5,
        seeding_rate_kg_ha=28.0,
        is_susceptible_to_disease=True,
        primary_disease="Northern Corn Leaf Blight",
    ),
    CropRotationEntry(
        field_code="F04",
        crop_name="Corn",
        crop_variety="DKC 64-87",
        planting_date=date(2025, 8, 1),
        expected_harvest_date=date(2026, 3, 5),
        is_perennial=False,
        expected_yield_tons_ha=10.8,
        seeding_rate_kg_ha=30.0,
        is_susceptible_to_disease=True,
        primary_disease="Common Rust",
    ),
    CropRotationEntry(
        field_code="F04",
        crop_name="Alfalfa",
        crop_variety="WL 354HQ",
        planting_date=date(2026, 4, 10),
        expected_harvest_date=date(2026, 5, 20),
        is_perennial=True,
        expected_yield_tons_ha=8.5,
        seeding_rate_kg_ha=18.0,
        is_susceptible_to_disease=True,
        primary_disease="Anthracnose",
    ),
    CropRotationEntry(
        field_code="F05",
        crop_name="Alfalfa",
        crop_variety="WL 319HQ",
        planting_date=date(2025, 6, 1),
        expected_harvest_date=date(2026, 5, 31),
        is_perennial=True,
        expected_yield_tons_ha=9.2,
        seeding_rate_kg_ha=20.0,
        is_susceptible_to_disease=True,
        primary_disease="Root Rot",
    ),
    CropRotationEntry(
        field_code="F06",
        crop_name="Barley",
        crop_variety="Conlon",
        planting_date=date(2025, 8, 20),
        expected_harvest_date=date(2026, 2, 28),
        is_perennial=False,
        expected_yield_tons_ha=5.5,
        seeding_rate_kg_ha=95.0,
        is_susceptible_to_disease=True,
        primary_disease="Net Blotch",
    ),
    CropRotationEntry(
        field_code="F06",
        crop_name="Soybean",
        crop_variety="P22A98X",
        planting_date=date(2026, 4, 15),
        expected_harvest_date=date(2026, 5, 22),
        is_perennial=False,
        expected_yield_tons_ha=2.8,
        seeding_rate_kg_ha=72.0,
        is_susceptible_to_disease=True,
        primary_disease="Brown Spot",
    ),
    CropRotationEntry(
        field_code="F07",
        crop_name="Potato",
        crop_variety="Russet Burbank",
        planting_date=date(2025, 8, 15),
        expected_harvest_date=date(2026, 3, 25),
        is_perennial=False,
        expected_yield_tons_ha=45.0,
        seeding_rate_kg_ha=None,
        is_susceptible_to_disease=True,
        primary_disease="Late Blight",
    ),
    CropRotationEntry(
        field_code="F08",
        crop_name="Apple",
        crop_variety="Honeycrisp",
        planting_date=date(2025, 6, 1),
        expected_harvest_date=date(2026, 5, 31),
        is_perennial=True,
        expected_yield_tons_ha=32.0,
        seeding_rate_kg_ha=None,
        is_susceptible_to_disease=True,
        primary_disease="Apple Scab",
    ),
    CropRotationEntry(
        field_code="F09",
        crop_name="Corn",
        crop_variety="P9918AM",
        planting_date=date(2025, 8, 8),
        expected_harvest_date=date(2026, 3, 12),
        is_perennial=False,
        expected_yield_tons_ha=12.2,
        seeding_rate_kg_ha=35.0,
        is_susceptible_to_disease=True,
        primary_disease="Goss's Wilt",
    ),
    CropRotationEntry(
        field_code="F10",
        crop_name="Soybean",
        crop_variety="AG43X6",
        planting_date=date(2025, 8, 12),
        expected_harvest_date=date(2026, 3, 18),
        is_perennial=False,
        expected_yield_tons_ha=4.1,
        seeding_rate_kg_ha=68.0,
        is_susceptible_to_disease=True,
        primary_disease="White Mold",
    ),
    CropRotationEntry(
        field_code="F01",
        crop_name="Cover Crop Oats",
        crop_variety="Everleaf 126",
        planting_date=date(2026, 4, 5),
        expected_harvest_date=date(2026, 5, 10),
        is_perennial=False,
        expected_yield_tons_ha=2.5,
        seeding_rate_kg_ha=85.0,
        is_susceptible_to_disease=False,
    ),
    CropRotationEntry(
        field_code="F05",
        crop_name="Alfalfa Cut 2",
        crop_variety="WL 319HQ",
        planting_date=date(2026, 2, 1),
        expected_harvest_date=date(2026, 4, 15),
        is_perennial=True,
        expected_yield_tons_ha=4.0,
        seeding_rate_kg_ha=None,
        is_susceptible_to_disease=True,
        primary_disease="Bacterial Wilt",
    ),
    CropRotationEntry(
        field_code="F08",
        crop_name="Apple Thinning Pass",
        crop_variety="Honeycrisp",
        planting_date=date(2026, 3, 1),
        expected_harvest_date=date(2026, 5, 15),
        is_perennial=True,
        expected_yield_tons_ha=28.0,
        seeding_rate_kg_ha=None,
        is_susceptible_to_disease=True,
        primary_disease="Fire Blight",
    ),
)

_CDD_DEV_MANIFEST = CDDManifest(
    profile_name="cdd-dev",
    farm_count=1,
    field_count=10,
    temporal_duration_days=365,
    farm=FarmDefinition(
        farm_code="AGRIFLOW-DEMO",
        farm_name="AGRIFLOW Demonstration Farm",
        owner_name="AGRIFLOW Synthetic Holdings LLC",
        country="United States",
        state="Iowa",
        city="Des Moines",
        latitude=41.88,
        longitude=-93.10,
        timezone="America/Chicago",
    ),
    fields=_FIELD_PORTFOLIO,
    crop_rotations=_CROP_ROTATIONS,
    sensor=SensorCadenceConfig(
        frequency_hours=1,
        sensor_types=(
            SensorType.SOIL_MOISTURE,
            SensorType.SOIL_TEMPERATURE,
            SensorType.AIR_TEMPERATURE,
            SensorType.AIR_HUMIDITY,
            SensorType.LEAF_WETNESS,
        ),
    ),
    weather=WeatherCadenceConfig(
        observations_per_day=4,
        hours_between_observations=6,
    ),
    satellite=SatelliteCadenceConfig(
        revisit_days=5,
        spectral_indices=(
            "NDVI",
            "EVI",
            "SAVI",
            "NDRE",
            "NDWI",
            "LAI",
            "GNDVI",
            "MSAVI",
        ),
        primary_provider="SENTINEL_2",
        supplementary_provider="LANDSAT_8",
        processing_level="L2A",
        resolution_m=10.0,
    ),
    disease=DiseaseFrequencyConfig(
        observations_per_crop=3,
        severity_distribution=(
            (DiseaseSeverity.LOW, 0.35),
            (DiseaseSeverity.MEDIUM, 0.35),
            (DiseaseSeverity.HIGH, 0.20),
            (DiseaseSeverity.CRITICAL, 0.10),
        ),
        diagnosis_methods=(
            DiagnosisMethod.VISUAL_INSPECTION,
            DiagnosisMethod.IMAGE_AI,
            DiagnosisMethod.AGRONOMIST,
            DiagnosisMethod.SENSOR_DETECTED,
        ),
    ),
    irrigation=IrrigationRulesConfig(
        season_start_month=4,
        season_end_month=10,
        deficit_hours_required=24,
        events_per_irrigated_field_min=8,
        events_per_irrigated_field_max=12,
        default_water_volume_liters=45000.0,
        default_duration_minutes=180.0,
    ),
    yield_rules=YieldRulesConfig(
        measurement_methods=(
            YieldMeasurementMethod.COMBINE_MONITOR,
            YieldMeasurementMethod.YIELD_MAP,
            YieldMeasurementMethod.MANUAL_SCALE,
            YieldMeasurementMethod.ESTIMATED,
        ),
        records_per_annual_crop=1,
        records_per_perennial_crop=2,
    ),
    season_phases=_SEASON_PHASES,
    target_row_counts={
        "farms": 1,
        "fields": 10,
        "soil_profiles": 10,
        "crops": 18,
        "weather_records": 14_600,
        "sensor_readings": 438_000,
        "irrigation_events": 96,
        "satellite_observations": 5_840,
        "disease_observations": 54,
        "yield_records": 22,
    },
)

_PROFILES: dict[str, CDDManifest] = {
    "cdd-dev": _CDD_DEV_MANIFEST,
}

# Planned profiles — register implementations in this module when ready.
# Factories and the orchestrator remain profile-agnostic; only manifest data changes.
FUTURE_PROFILES: dict[str, str] = {
    "cdd-demo": (
        "Stakeholder demonstration profile — same AGRIFLOW Demonstration Farm topology "
        "with reduced temporal horizon or subset domains for fast demo reload."
    ),
    "cdd-benchmark": (
        "Compression and query performance profile — 15-minute sensor cadence targeting "
        "~4.4M sensor rows per ADR-003 benchmark scenarios."
    ),
    "cdd-large": (
        "Production-scale simulation profile — 100 farms, 1,000 fields for Phase 16+ "
        "Digital Twin and load testing."
    ),
}


def register_profile(manifest: CDDManifest) -> None:
    """
    Register a new dataset profile.

    Adding a profile requires only a new ``CDDManifest`` instance and a call to this
    function from ``manifest.py``. Factories and the orchestrator require no changes.
    """
    _PROFILES[manifest.profile_name] = manifest


def expected_total_row_count(manifest: CDDManifest) -> int:
    """Sum of per-domain target row counts declared in the manifest."""
    return sum(manifest.target_row_counts.values())


def get_manifest(profile: str | None = None) -> CDDManifest:
    """Return the manifest for the requested profile (default: cdd-dev)."""
    name = profile or DEFAULT_PROFILE
    if name not in _PROFILES:
        available = ", ".join(sorted(_PROFILES))
        raise ValueError(f"Unknown CDD profile {name!r}. Available: {available}")
    return _PROFILES[name]


def list_profiles() -> tuple[str, ...]:
    """Return registered (implemented) profile names."""
    return tuple(sorted(_PROFILES))


def list_future_profiles() -> tuple[str, ...]:
    """Return planned profile names not yet registered."""
    return tuple(sorted(FUTURE_PROFILES))
