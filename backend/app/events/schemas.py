"""Versioned domain event payload schemas (Phase 14)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import (
    AlertSeverity,
    AlertType,
    DiagnosisMethod,
    DiseaseSeverity,
    IrrigationMethod,
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
    SatelliteProvider,
    SensorType,
    SpectralIndex,
    WaterSource,
    YieldMeasurementMethod,
)
from app.db.models.crop import CropStatus


class SensorReadingCreatedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sensor_reading_id: UUID
    field_id: UUID
    sensor_type: SensorType
    sensor_value: float
    unit: str
    recorded_at: datetime
    notes: str | None = None


class WeatherRecordCreatedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weather_record_id: UUID
    field_id: UUID
    recorded_at: datetime
    data_source: str | None = None


class IrrigationCompletedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    irrigation_event_id: UUID
    field_id: UUID
    irrigation_method: IrrigationMethod
    water_source: WaterSource | None = None
    started_at: datetime
    ended_at: datetime | None = None
    duration_minutes: float | None = None
    water_volume_liters: float | None = None


class YieldRecordedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    yield_record_id: UUID
    crop_id: UUID
    field_id: UUID
    recorded_at: datetime
    yield_value_tons_ha: float
    measurement_method: YieldMeasurementMethod


class DiseaseObservedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    disease_observation_id: UUID
    crop_id: UUID
    field_id: UUID
    observed_at: datetime
    disease_name: str
    severity: DiseaseSeverity
    diagnosis_method: DiagnosisMethod


class SatelliteObservedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    satellite_observation_id: UUID
    field_id: UUID
    observed_at: datetime
    spectral_index: SpectralIndex
    index_value: float
    satellite_provider: SatelliteProvider


class CropLifecycleChangedPayloadV1(BaseModel):
    crop_id: UUID
    field_id: UUID
    previous_status: CropStatus
    new_status: CropStatus
    changed_at: datetime


class RecommendationCreatedPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recommendation_id: UUID
    field_id: UUID
    crop_id: UUID | None = None
    recommendation_type: RecommendationType
    status: RecommendationStatus
    priority: RecommendationPriority
    title: str
    confidence_score: float | None = None
    engine_version: str | None = None
    valid_from: datetime
    valid_until: datetime | None = None


class AlertTriggeredPayloadV1(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    alert_id: UUID
    field_id: UUID
    crop_id: UUID | None = None
    recommendation_id: UUID | None = None
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    triggered_at: datetime
    is_acknowledged: bool = False


class DomainEventEnvelopeV1(BaseModel):
    """Wire format published to Redpanda and stored in the outbox ``payload`` column."""

    event_id: UUID = Field(description="Outbox row id — unique message idempotency key")
    event_type: str
    schema_version: str
    occurred_at: datetime
    aggregate_type: str
    aggregate_id: UUID
    payload: dict
