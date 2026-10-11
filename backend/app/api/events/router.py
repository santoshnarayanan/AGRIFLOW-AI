"""Domain event catalog API (Phase 14)."""

from fastapi import APIRouter

from app.events.catalog import EVENT_CATALOG
from app.schemas.domain_event import EventCatalogItemResponse, EventCatalogResponse

router = APIRouter(prefix="/events", tags=["Domain Events"])


@router.get("/catalog", response_model=EventCatalogResponse)
async def get_event_catalog() -> EventCatalogResponse:
    """Return registered domain event types, topics, and schema versions."""
    items = [
        EventCatalogItemResponse(
            event_type=entry.event_type.value,
            topic=entry.topic,
            schema_version=entry.schema_version,
            description=entry.description,
        )
        for entry in EVENT_CATALOG.values()
    ]
    items.sort(key=lambda i: i.event_type)
    return EventCatalogResponse(events=items, count=len(items))
