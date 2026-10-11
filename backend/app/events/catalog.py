"""Event catalog — maps event types to Redpanda/Kafka topics (Phase 14)."""

from dataclasses import dataclass

from app.events.types import DomainEventType


@dataclass(frozen=True, slots=True)
class EventCatalogEntry:
    event_type: DomainEventType
    topic: str
    schema_version: str
    description: str


EVENT_CATALOG: dict[DomainEventType, EventCatalogEntry] = {
    DomainEventType.SENSOR_READING_CREATED: EventCatalogEntry(
        event_type=DomainEventType.SENSOR_READING_CREATED,
        topic="agriflow.domain.sensor-reading-created.v1",
        schema_version="1.0",
        description="Append-only IoT telemetry persisted for a field.",
    ),
    DomainEventType.WEATHER_RECORD_CREATED: EventCatalogEntry(
        event_type=DomainEventType.WEATHER_RECORD_CREATED,
        topic="agriflow.domain.weather-record-created.v1",
        schema_version="1.0",
        description="Climate observation recorded for a field.",
    ),
    DomainEventType.IRRIGATION_COMPLETED: EventCatalogEntry(
        event_type=DomainEventType.IRRIGATION_COMPLETED,
        topic="agriflow.domain.irrigation-completed.v1",
        schema_version="1.0",
        description="Irrigation event closed or logged as completed.",
    ),
    DomainEventType.YIELD_RECORDED: EventCatalogEntry(
        event_type=DomainEventType.YIELD_RECORDED,
        topic="agriflow.domain.yield-recorded.v1",
        schema_version="1.0",
        description="Harvest yield measurement logged for a crop cycle.",
    ),
    DomainEventType.DISEASE_OBSERVED: EventCatalogEntry(
        event_type=DomainEventType.DISEASE_OBSERVED,
        topic="agriflow.domain.disease-observed.v1",
        schema_version="1.0",
        description="Plant health observation recorded for a crop.",
    ),
    DomainEventType.SATELLITE_OBSERVED: EventCatalogEntry(
        event_type=DomainEventType.SATELLITE_OBSERVED,
        topic="agriflow.domain.satellite-observed.v1",
        schema_version="1.0",
        description="Spectral index observation ingested for a field.",
    ),
    DomainEventType.CROP_LIFECYCLE_CHANGED: EventCatalogEntry(
        event_type=DomainEventType.CROP_LIFECYCLE_CHANGED,
        topic="agriflow.domain.crop-lifecycle-changed.v1",
        schema_version="1.0",
        description="Crop status transition (e.g. PLANTED → GROWING).",
    ),
}


def get_catalog_entry(event_type: DomainEventType) -> EventCatalogEntry:
    return EVENT_CATALOG[event_type]
