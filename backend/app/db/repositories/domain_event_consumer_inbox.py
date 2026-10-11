"""Idempotency ledger for domain event consumers (Phase 14)."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.domain_event_consumer_inbox import DomainEventConsumerInbox
from app.db.repositories.base import BaseRepository


class DomainEventConsumerInboxRepository(BaseRepository[DomainEventConsumerInbox]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DomainEventConsumerInbox, session)

    async def try_claim(
        self,
        *,
        event_id: uuid.UUID,
        consumer_group_id: str,
        event_type: str,
    ) -> bool:
        """
        Record first-time processing for this consumer group.

        Returns True if this call claimed the event; False if already processed.
        """
        stmt = (
            insert(DomainEventConsumerInbox)
            .values(
                event_id=event_id,
                consumer_group_id=consumer_group_id,
                event_type=event_type,
            )
            .on_conflict_do_nothing(
                index_elements=["event_id", "consumer_group_id"],
            )
            .returning(DomainEventConsumerInbox.id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def count_processed(self) -> int:
        total = await self._session.scalar(
            select(func.count()).select_from(DomainEventConsumerInbox)
        )
        return int(total or 0)
