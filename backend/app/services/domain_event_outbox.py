"""Read-only outbox queries for operations API (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.db.models.domain_event_outbox import DomainEventOutbox
from app.db.repositories.domain_event_consumer_inbox import (
    DomainEventConsumerInboxRepository,
)
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository


class DomainEventOutboxService:
    def __init__(
        self,
        outbox_repository: DomainEventOutboxRepository,
        consumer_inbox_repository: DomainEventConsumerInboxRepository,
    ) -> None:
        self._outbox = outbox_repository
        self._consumer_inbox = consumer_inbox_repository

    async def get_stats(self) -> dict[str, int]:
        stats = await self._outbox.get_stats()
        stats["events_processed"] = await self._consumer_inbox.count_processed()
        return stats

    async def list_entries(
        self,
        *,
        status: str = "pending",
        limit: int = 50,
    ) -> list[DomainEventOutbox]:
        return await self._outbox.list_by_status(status=status, limit=limit)

    async def get_entry(self, outbox_id: uuid.UUID) -> DomainEventOutbox | None:
        return await self._outbox.get_by_id(outbox_id)

    async def replay_entry(self, outbox_id: uuid.UUID) -> DomainEventOutbox | None:
        """Re-queue a single outbox row for the relay worker."""
        return await self._outbox.requeue_for_relay(outbox_id)

    async def replay_entries(self, outbox_ids: list[uuid.UUID]) -> list[uuid.UUID]:
        """Re-queue many rows; returns ids that were found and reset."""
        replayed: list[uuid.UUID] = []
        for outbox_id in outbox_ids:
            row = await self._outbox.requeue_for_relay(outbox_id)
            if row is not None:
                replayed.append(outbox_id)
        return replayed
