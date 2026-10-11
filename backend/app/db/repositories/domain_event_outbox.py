"""Outbox repository — enqueue and relay lifecycle (Phase 14)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.domain_event_outbox import DomainEventOutbox
from app.db.repositories.base import BaseRepository


class DomainEventOutboxRepository(BaseRepository[DomainEventOutbox]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(DomainEventOutbox, session)

    async def enqueue(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: uuid.UUID,
        topic: str,
        payload: dict[str, Any],
    ) -> DomainEventOutbox:
        return await self.create(
            {
                "event_type": event_type,
                "aggregate_type": aggregate_type,
                "aggregate_id": aggregate_id,
                "topic": topic,
                "payload": payload,
            }
        )

    async def get_stats(self) -> dict[str, int]:
        pending = await self._session.scalar(
            select(func.count())
            .select_from(DomainEventOutbox)
            .where(DomainEventOutbox.published_at.is_(None))
        )
        published = await self._session.scalar(
            select(func.count())
            .select_from(DomainEventOutbox)
            .where(DomainEventOutbox.published_at.is_not(None))
        )
        failed = await self._session.scalar(
            select(func.count())
            .select_from(DomainEventOutbox)
            .where(
                DomainEventOutbox.published_at.is_(None),
                DomainEventOutbox.publish_attempts > 0,
            )
        )
        return {
            "pending": int(pending or 0),
            "published": int(published or 0),
            "failed": int(failed or 0),
            "total": int((pending or 0) + (published or 0)),
        }

    async def list_by_status(
        self,
        *,
        status: str = "pending",
        limit: int = 50,
    ) -> list[DomainEventOutbox]:
        query = select(DomainEventOutbox).order_by(DomainEventOutbox.created_at.desc())
        if status == "pending":
            query = query.where(DomainEventOutbox.published_at.is_(None))
        elif status == "published":
            query = query.where(DomainEventOutbox.published_at.is_not(None))
        elif status == "failed":
            query = query.where(
                DomainEventOutbox.published_at.is_(None),
                DomainEventOutbox.publish_attempts > 0,
            )
        elif status != "all":
            raise ValueError(f"Unsupported outbox status filter: {status}")
        result = await self._session.execute(query.limit(limit))
        return list(result.scalars().all())

    async def list_pending(self, *, limit: int = 100) -> list[DomainEventOutbox]:
        result = await self._session.execute(
            select(DomainEventOutbox)
            .where(DomainEventOutbox.published_at.is_(None))
            .order_by(DomainEventOutbox.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def mark_published(self, outbox_id: uuid.UUID) -> None:
        await self._session.execute(
            update(DomainEventOutbox)
            .where(DomainEventOutbox.id == outbox_id)
            .values(published_at=datetime.now(timezone.utc))
        )
        await self._session.flush()

    async def mark_failed(self, outbox_id: uuid.UUID, error: str) -> None:
        row = await self.get_by_id(outbox_id)
        if row is None:
            return
        await self._session.execute(
            update(DomainEventOutbox)
            .where(DomainEventOutbox.id == outbox_id)
            .values(
                publish_attempts=row.publish_attempts + 1,
                last_error=error[:4000],
            )
        )
        await self._session.flush()
