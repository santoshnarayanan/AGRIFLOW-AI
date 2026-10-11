"""Domain event type registry (Phase 14)."""

from enum import StrEnum


class DomainEventType(StrEnum):
    """Business-significant events published to the enterprise stream."""

    SENSOR_READING_CREATED = "SensorReadingCreated"
    WEATHER_RECORD_CREATED = "WeatherRecordCreated"
    IRRIGATION_COMPLETED = "IrrigationCompleted"
    YIELD_RECORDED = "YieldRecorded"
    DISEASE_OBSERVED = "DiseaseObserved"
    SATELLITE_OBSERVED = "SatelliteObserved"
    CROP_LIFECYCLE_CHANGED = "CropLifecycleChanged"


class AggregateType(StrEnum):
    """Aggregate root names referenced in the outbox and event envelope."""

    SENSOR_READING = "sensor_reading"
    WEATHER_RECORD = "weather_record"
    IRRIGATION_EVENT = "irrigation_event"
    YIELD_RECORD = "yield_record"
    DISEASE_OBSERVATION = "disease_observation"
    SATELLITE_OBSERVATION = "satellite_observation"
    CROP = "crop"
