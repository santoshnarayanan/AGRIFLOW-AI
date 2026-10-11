"""Read-only outbox queries for operations API (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime

from app.db.models.domain_event_outbox import DomainEventOutbox
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository


class DomainEventOutboxService:
    def __init__(self, outbox_repository: DomainEventOutboxRepository) -> None:
        self._outbox = outbox_repository

    async def get_stats(self) -> dict[str, int]:
        return await self._outbox.get_stats()

    async def list_entries(
        self,
        *,
        status: str = "pending",
        limit: int = 50,
    ) -> list[DomainEventOutbox]:
        return await self._outbox.list_by_status(status=status, limit=limit)

    async def get_entry(self, outbox_id: uuid.UUID) -> DomainEventOutbox | None:
        return await self._outbox.get_by_id(outbox_id)
