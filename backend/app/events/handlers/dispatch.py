"""Fan-out domain event handling to Phase 14 business handlers."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.events.handlers import alert_evaluation, ml_engine_evaluation
from app.events.schemas import DomainEventEnvelopeV1


async def handle_domain_event(session: AsyncSession, envelope: DomainEventEnvelopeV1) -> None:
    await alert_evaluation.handle_domain_event(session, envelope)
    await ml_engine_evaluation.handle_domain_event(session, envelope)
