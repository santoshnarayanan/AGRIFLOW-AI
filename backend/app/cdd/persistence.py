"""
CDD persistence layer — isolated ORM writes for generated datasets.

Persists in-memory CDD records to PostgreSQL using SQLAlchemy ORM with FK-safe
ordering. Does not use repositories or services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.cdd.types import (
    CDDCropRecord,
    CDDDataset,
    CDDDiseaseObservationRecord,
    CDDFarmRecord,
    CDDFieldRecord,
    CDDIrrigationEventRecord,
    CDDSatelliteObservationRecord,
    CDDSensorReadingRecord,
    CDDSoilProfileRecord,
    CDDWeatherRecord,
    CDDYieldRecord,
)
from app.db.models.crop import Crop
from app.db.models.disease_observation import DiseaseObservation
from app.db.models.farm import Farm
from app.db.models.field import Field
from app.db.models.irrigation_event import IrrigationEvent
from app.db.models.satellite_observation import SatelliteObservation
from app.db.models.sensor_reading import SensorReading
from app.db.models.soil_profile import SoilProfile
from app.db.models.weather_record import WeatherRecord
from app.db.models.yield_record import YieldRecord

logger = logging.getLogger(__name__)

# Batch size for high-volume hypertable domains.
_BATCH_SIZE: int = 5_000


@dataclass(frozen=True, slots=True)
class PersistenceResult:
    """Per-domain row counts written during a persistence execution."""

    row_counts: dict[str, int]

    @property
    def total_rows(self) -> int:
        return sum(self.row_counts.values())


def _farm_mapping(record: CDDFarmRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "farm_code": record.farm_code,
        "farm_name": record.farm_name,
        "owner_name": record.owner_name,
        "country": record.country,
        "state": record.state,
        "city": record.city,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "total_area_hectares": record.total_area_hectares,
        "is_active": record.is_active,
    }


def _field_mapping(record: CDDFieldRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "farm_id": record.farm_id,
        "name": record.name,
        "area_hectares": record.area_hectares,
        "soil_type": record.soil_type,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "elevation_m": record.elevation_m,
    }


def _soil_profile_mapping(record: CDDSoilProfileRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "soil_type": record.soil_type,
        "ph": record.ph,
        "organic_matter": record.organic_matter,
        "nitrogen": record.nitrogen,
        "phosphorus": record.phosphorus,
        "potassium": record.potassium,
        "soil_depth_cm": record.soil_depth_cm,
        "cation_exchange_capacity_meq": record.cation_exchange_capacity_meq,
        "notes": record.notes,
    }


def _crop_mapping(record: CDDCropRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "crop_name": record.crop_name,
        "crop_variety": record.crop_variety,
        "planting_date": record.planting_date,
        "expected_harvest_date": record.expected_harvest_date,
        "actual_harvest_date": record.actual_harvest_date,
        "status": record.status,
        "expected_yield_tons_ha": record.expected_yield_tons_ha,
        "actual_yield_tons_ha": record.actual_yield_tons_ha,
        "seeding_rate_kg_ha": record.seeding_rate_kg_ha,
        "growth_stage": record.growth_stage,
    }


def _weather_mapping(record: CDDWeatherRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "recorded_at": record.recorded_at,
        "temperature_c": record.temperature_c,
        "humidity_percent": record.humidity_percent,
        "rainfall_mm": record.rainfall_mm,
        "wind_speed_kmh": record.wind_speed_kmh,
        "solar_radiation_wm2": record.solar_radiation_wm2,
        "temperature_min_c": record.temperature_min_c,
        "temperature_max_c": record.temperature_max_c,
        "data_source": record.data_source,
    }


def _sensor_mapping(record: CDDSensorReadingRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "sensor_type": record.sensor_type,
        "sensor_value": record.sensor_value,
        "unit": record.unit,
        "recorded_at": record.recorded_at,
        "notes": record.notes,
    }


def _satellite_mapping(record: CDDSatelliteObservationRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "observed_at": record.observed_at,
        "satellite_provider": record.satellite_provider,
        "processing_level": record.processing_level,
        "spectral_index": record.spectral_index,
        "index_value": record.index_value,
        "cloud_cover_percent": record.cloud_cover_percent,
        "resolution_m": record.resolution_m,
        "scene_id": record.scene_id,
        "source_url": record.source_url,
        "notes": record.notes,
    }


def _irrigation_mapping(record: CDDIrrigationEventRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "field_id": record.field_id,
        "started_at": record.started_at,
        "ended_at": record.ended_at,
        "duration_minutes": record.duration_minutes,
        "water_volume_liters": record.water_volume_liters,
        "irrigation_method": record.irrigation_method,
        "water_source": record.water_source,
        "notes": record.notes,
    }


def _disease_mapping(record: CDDDiseaseObservationRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "crop_id": record.crop_id,
        "field_id": record.field_id,
        "observed_at": record.observed_at,
        "disease_name": record.disease_name,
        "severity": record.severity,
        "affected_area_percent": record.affected_area_percent,
        "diagnosis_method": record.diagnosis_method,
        "treatment_applied": record.treatment_applied,
        "notes": record.notes,
    }


def _yield_mapping(record: CDDYieldRecord) -> dict[str, object]:
    return {
        "id": record.id,
        "crop_id": record.crop_id,
        "field_id": record.field_id,
        "recorded_at": record.recorded_at,
        "yield_value_tons_ha": record.yield_value_tons_ha,
        "measurement_method": record.measurement_method,
        "area_harvested_ha": record.area_harvested_ha,
        "moisture_content_percent": record.moisture_content_percent,
        "test_weight_kg_hl": record.test_weight_kg_hl,
        "quality_grade": record.quality_grade,
        "notes": record.notes,
    }


async def _persist_batch(
    session: AsyncSession,
    model: type,
    mappings: list[dict[str, object]],
    *,
    domain: str,
) -> int:
    """Insert rows in batches via ORM bulk mappings; returns total rows added."""
    if not mappings:
        return 0

    total = 0

    def _bulk_insert(sync_session, batch: list[dict[str, object]]) -> None:
        sync_session.bulk_insert_mappings(model, batch)

    for offset in range(0, len(mappings), _BATCH_SIZE):
        batch = mappings[offset : offset + _BATCH_SIZE]
        await session.run_sync(_bulk_insert, batch)
        total += len(batch)
        logger.debug(
            "CDD persistence batch committed",
            extra={"domain": domain, "batch_size": len(batch), "total_persisted": total},
        )

    return total


async def persist_cdd_dataset(
    session: AsyncSession,
    dataset: CDDDataset,
) -> PersistenceResult:
    """
    Persist a validated in-memory dataset using FK-safe ordering.

    All inserts occur within a single transaction. Rolls back on any failure.
    """
    row_counts: dict[str, int] = {}

    logger.info(
        "CDD persistence starting",
        extra={
            "cdd_version": dataset.version,
            "profile": dataset.profile,
            "total_rows": dataset.total_row_count,
        },
    )

    try:
        # 1. farms
        row_counts["farms"] = await _persist_batch(
            session,
            Farm,
            [_farm_mapping(r) for r in dataset.farms],
            domain="farms",
        )

        # 2. fields
        row_counts["fields"] = await _persist_batch(
            session,
            Field,
            [_field_mapping(r) for r in dataset.fields],
            domain="fields",
        )

        # 3. soil_profiles + crops
        row_counts["soil_profiles"] = await _persist_batch(
            session,
            SoilProfile,
            [_soil_profile_mapping(r) for r in dataset.soil_profiles],
            domain="soil_profiles",
        )
        row_counts["crops"] = await _persist_batch(
            session,
            Crop,
            [_crop_mapping(r) for r in dataset.crops],
            domain="crops",
        )

        # 4. time-series and field-scoped measurements
        row_counts["weather_records"] = await _persist_batch(
            session,
            WeatherRecord,
            [_weather_mapping(r) for r in dataset.weather_records],
            domain="weather_records",
        )
        row_counts["sensor_readings"] = await _persist_batch(
            session,
            SensorReading,
            [_sensor_mapping(r) for r in dataset.sensor_readings],
            domain="sensor_readings",
        )
        row_counts["satellite_observations"] = await _persist_batch(
            session,
            SatelliteObservation,
            [_satellite_mapping(r) for r in dataset.satellite_observations],
            domain="satellite_observations",
        )
        row_counts["irrigation_events"] = await _persist_batch(
            session,
            IrrigationEvent,
            [_irrigation_mapping(r) for r in dataset.irrigation_events],
            domain="irrigation_events",
        )

        # 5. crop-anchored observations
        row_counts["disease_observations"] = await _persist_batch(
            session,
            DiseaseObservation,
            [_disease_mapping(r) for r in dataset.disease_observations],
            domain="disease_observations",
        )
        row_counts["yield_records"] = await _persist_batch(
            session,
            YieldRecord,
            [_yield_mapping(r) for r in dataset.yield_records],
            domain="yield_records",
        )

        await session.commit()

        result = PersistenceResult(row_counts=row_counts)
        logger.info(
            "CDD persistence committed",
            extra={"total_persisted": result.total_rows, "domains": row_counts},
        )
        return result

    except Exception:
        await session.rollback()
        logger.exception("CDD persistence failed — transaction rolled back")
        raise
