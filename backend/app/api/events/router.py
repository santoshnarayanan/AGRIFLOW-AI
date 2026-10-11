"""Domain event catalog and outbox operations API (Phase 14)."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DomainEventOutboxServiceDep
from app.core.security.platform_auth import PlatformOperatorDep
from app.events.catalog import EVENT_CATALOG
from app.schemas.domain_event import (
    EventCatalogItemResponse,
    EventCatalogResponse,
    OutboxEntryListResponse,
    OutboxEntryResponse,
    OutboxReplayRequest,
    OutboxReplayResponse,
    OutboxStatsResponse,
)

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


@router.get("/outbox/stats", response_model=OutboxStatsResponse)
async def get_outbox_stats(
    outbox_service: DomainEventOutboxServiceDep,
    _: PlatformOperatorDep,
) -> OutboxStatsResponse:
    """Operational counts for the transactional outbox (pending / published / failed)."""
    stats = await outbox_service.get_stats()
    return OutboxStatsResponse(**stats)


@router.get("/outbox/entries", response_model=OutboxEntryListResponse)
async def list_outbox_entries(
    outbox_service: DomainEventOutboxServiceDep,
    _: PlatformOperatorDep,
    status: str = Query(
        default="pending",
        pattern="^(pending|published|failed|all)$",
        description="Filter by publish state",
    ),
    limit: int = Query(default=50, ge=1, le=200),
) -> OutboxEntryListResponse:
    """List recent outbox rows for operations dashboards."""
    rows = await outbox_service.list_entries(status=status, limit=limit)
    entries = [
        OutboxEntryResponse(
            id=row.id,
            event_type=row.event_type,
            aggregate_type=row.aggregate_type,
            aggregate_id=row.aggregate_id,
            topic=row.topic,
            created_at=row.created_at,
            published_at=row.published_at,
            publish_attempts=row.publish_attempts,
            last_error=row.last_error,
        )
        for row in rows
    ]
    return OutboxEntryListResponse(entries=entries, count=len(entries))


@router.get("/outbox/entries/{outbox_id}", response_model=OutboxEntryResponse)
async def get_outbox_entry(
    outbox_id: UUID,
    outbox_service: DomainEventOutboxServiceDep,
    _: PlatformOperatorDep,
) -> OutboxEntryResponse:
    """Return a single outbox row including full envelope payload metadata."""
    row = await outbox_service.get_entry(outbox_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outbox entry '{outbox_id}' not found.",
        )
    return OutboxEntryResponse(
        id=row.id,
        event_type=row.event_type,
        aggregate_type=row.aggregate_type,
        aggregate_id=row.aggregate_id,
        topic=row.topic,
        created_at=row.created_at,
        published_at=row.published_at,
        publish_attempts=row.publish_attempts,
        last_error=row.last_error,
    )


@router.post(
    "/outbox/entries/{outbox_id}/replay",
    response_model=OutboxReplayResponse,
)
async def replay_outbox_entry(
    outbox_id: UUID,
    outbox_service: DomainEventOutboxServiceDep,
    _: PlatformOperatorDep,
) -> OutboxReplayResponse:
    """Reset publish state so the relay re-sends the stored envelope to Redpanda."""
    row = await outbox_service.replay_entry(outbox_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Outbox entry '{outbox_id}' not found.",
        )
    return OutboxReplayResponse(replayed_ids=[outbox_id], count=1)


@router.post("/outbox/replay", response_model=OutboxReplayResponse)
async def replay_outbox_entries(
    body: OutboxReplayRequest,
    outbox_service: DomainEventOutboxServiceDep,
    _: PlatformOperatorDep,
) -> OutboxReplayResponse:
    """Batch replay for operations backfill."""
    replayed = await outbox_service.replay_entries(body.outbox_ids)
    return OutboxReplayResponse(replayed_ids=replayed, count=len(replayed))
