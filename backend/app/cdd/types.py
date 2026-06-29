"""
CDD domain record types.

Plain dataclasses representing generated entities prior to persistence.
Shapes mirror ORM models without audit timestamps.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.core.enums import (
    DiagnosisMethod,
    DiseaseSeverity,
    IrrigationMethod,
    ProcessingLevel,
    SatelliteProvider,
    SensorType,
    SpectralIndex,
    WaterSource,
    YieldMeasurementMethod,
)
from app.db.models.crop import CropStatus
from app.db.models.soil_profile import SoilType

if TYPE_CHECKING:
    from app.cdd.manifest import CDDManifest


@dataclass(frozen=True, slots=True)
class CDDFarmRecord:
    id: uuid.UUID
    farm_code: str
    farm_name: str
    owner_name: str
    country: str
    state: str
    city: str
    latitude: float
    longitude: float
    total_area_hectares: float
    is_active: bool = True


@dataclass(frozen=True, slots=True)
class CDDFieldRecord:
    id: uuid.UUID
    farm_id: uuid.UUID
    field_code: str
    name: str
    area_hectares: float
    soil_type: str
    latitude: float
    longitude: float
    elevation_m: float
    irrigation_method: IrrigationMethod | None
    is_irrigated: bool


@dataclass(frozen=True, slots=True)
class CDDSoilProfileRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    soil_type: SoilType
    ph: float
    organic_matter: float
    nitrogen: float
    phosphorus: float
    potassium: float
    soil_depth_cm: float
    cation_exchange_capacity_meq: float
    infiltration_rate_mm_hr: float
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDCropRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    field_code: str
    crop_name: str
    crop_variety: str | None
    planting_date: date
    expected_harvest_date: date | None
    actual_harvest_date: date | None
    status: CropStatus
    expected_yield_tons_ha: float
    actual_yield_tons_ha: float | None
    seeding_rate_kg_ha: float | None
    growth_stage: str | None
    is_perennial: bool = False
    is_susceptible_to_disease: bool = True


@dataclass(frozen=True, slots=True)
class CDDWeatherRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    recorded_at: datetime
    temperature_c: Decimal
    humidity_percent: Decimal
    rainfall_mm: Decimal
    wind_speed_kmh: Decimal
    solar_radiation_wm2: Decimal | None
    temperature_min_c: Decimal | None
    temperature_max_c: Decimal | None
    data_source: str = "CDD"


@dataclass(frozen=True, slots=True)
class CDDSensorReadingRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    sensor_type: SensorType
    sensor_value: float
    unit: str
    recorded_at: datetime
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDIrrigationEventRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None
    duration_minutes: Decimal | None
    water_volume_liters: Decimal | None
    irrigation_method: IrrigationMethod
    water_source: WaterSource | None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDSatelliteObservationRecord:
    id: uuid.UUID
    field_id: uuid.UUID
    observed_at: datetime
    satellite_provider: SatelliteProvider
    processing_level: ProcessingLevel
    spectral_index: SpectralIndex
    index_value: Decimal
    cloud_cover_percent: Decimal | None
    resolution_m: Decimal | None
    scene_id: str | None = None
    source_url: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDDiseaseObservationRecord:
    id: uuid.UUID
    crop_id: uuid.UUID
    field_id: uuid.UUID
    observed_at: datetime
    disease_name: str
    severity: DiseaseSeverity
    affected_area_percent: Decimal | None
    diagnosis_method: DiagnosisMethod
    treatment_applied: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDYieldRecord:
    id: uuid.UUID
    crop_id: uuid.UUID
    field_id: uuid.UUID
    recorded_at: datetime
    yield_value_tons_ha: Decimal
    measurement_method: YieldMeasurementMethod
    area_harvested_ha: Decimal | None = None
    moisture_content_percent: Decimal | None = None
    test_weight_kg_hl: Decimal | None = None
    quality_grade: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CDDDatasetMetadata:
    """
    Session-level metadata describing a generated in-memory dataset.

    Populated after generation and before persistence validation. Does not imply
    database storage or execution timing measurement.
    """

    generator_version: str
    manifest_profile: str
    dataset_version: str
    seed: int
    generated_at: datetime
    temporal_start: datetime
    temporal_end: datetime
    expected_row_count: int
    actual_row_count: int
    domain_row_counts: dict[str, int]
    generation_duration_ms: int | None = None
    notes: str | None = None

    @classmethod
    def from_dataset(
        cls,
        dataset: CDDDataset,
        *,
        manifest: CDDManifest | None = None,
        generated_at: datetime | None = None,
        generation_duration_ms: int | None = None,
        notes: str | None = None,
    ) -> CDDDatasetMetadata:
        """
        Build metadata from an in-memory dataset and optional manifest.

        ``generation_duration_ms`` is a placeholder for Step 2C-C timing capture.
        """
        from app.cdd.config import (
            CDD_GENERATOR_VERSION,
            TEMPORAL_END,
            TEMPORAL_START,
        )
        from app.cdd.manifest import expected_total_row_count, get_manifest

        resolved_manifest = manifest or get_manifest(dataset.profile)
        expected = expected_total_row_count(resolved_manifest)
        actual = dataset.total_row_count

        return cls(
            generator_version=CDD_GENERATOR_VERSION,
            manifest_profile=dataset.profile,
            dataset_version=dataset.version,
            seed=dataset.seed,
            generated_at=generated_at or datetime.now(tz=TEMPORAL_START.tzinfo),
            temporal_start=TEMPORAL_START,
            temporal_end=TEMPORAL_END,
            expected_row_count=expected,
            actual_row_count=actual,
            domain_row_counts=dataset.domain_row_counts(),
            generation_duration_ms=generation_duration_ms,
            notes=notes,
        )


@dataclass(slots=True)
class CDDDataset:
    """
    Complete generated dataset bundle returned by the orchestrator.

    Domain lists hold in-memory records prior to persistence. Attach session
    metadata via :meth:`attach_metadata` after generation completes.
    """

    version: str
    profile: str
    seed: int
    metadata: CDDDatasetMetadata | None = None
    farms: list[CDDFarmRecord] = field(default_factory=list)
    fields: list[CDDFieldRecord] = field(default_factory=list)
    soil_profiles: list[CDDSoilProfileRecord] = field(default_factory=list)
    crops: list[CDDCropRecord] = field(default_factory=list)
    weather_records: list[CDDWeatherRecord] = field(default_factory=list)
    sensor_readings: list[CDDSensorReadingRecord] = field(default_factory=list)
    satellite_observations: list[CDDSatelliteObservationRecord] = field(
        default_factory=list
    )
    irrigation_events: list[CDDIrrigationEventRecord] = field(default_factory=list)
    disease_observations: list[CDDDiseaseObservationRecord] = field(
        default_factory=list
    )
    yield_records: list[CDDYieldRecord] = field(default_factory=list)

    def domain_row_counts(self) -> dict[str, int]:
        """Per-domain record counts for validation and metadata."""
        return {
            "farms": len(self.farms),
            "fields": len(self.fields),
            "soil_profiles": len(self.soil_profiles),
            "crops": len(self.crops),
            "weather_records": len(self.weather_records),
            "sensor_readings": len(self.sensor_readings),
            "satellite_observations": len(self.satellite_observations),
            "irrigation_events": len(self.irrigation_events),
            "disease_observations": len(self.disease_observations),
            "yield_records": len(self.yield_records),
        }

    def attach_metadata(
        self,
        *,
        manifest: CDDManifest | None = None,
        generated_at: datetime | None = None,
        generation_duration_ms: int | None = None,
        notes: str | None = None,
    ) -> CDDDatasetMetadata:
        """Build and attach session metadata to this dataset."""
        self.metadata = CDDDatasetMetadata.from_dataset(
            self,
            manifest=manifest,
            generated_at=generated_at,
            generation_duration_ms=generation_duration_ms,
            notes=notes,
        )
        return self.metadata

    @property
    def total_row_count(self) -> int:
        return sum(self.domain_row_counts().values())
