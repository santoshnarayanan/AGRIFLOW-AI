"""
Business domain-event consumer (Phase 14).

Runs alert evaluation and future projection handlers against the event stream.

    python -m app.events.business_consumer
"""

from __future__ import annotations

import asyncio
import json
import signal

from aiokafka import AIOKafkaConsumer
from pydantic import ValidationError

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories.domain_event_consumer_inbox import (
    DomainEventConsumerInboxRepository,
)
from app.db.session import AsyncSessionFactory
from app.events.catalog import EVENT_CATALOG
from app.events.handlers.alert_evaluation import handle_domain_event
from app.events.schemas import DomainEventEnvelopeV1

logger = get_logger(__name__)


class DomainEventBusinessConsumer:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = True

    async def run(self) -> None:
        if not self._settings.REDPANDA_ENABLED:
            logger.warning("business_consumer.redpanda_disabled")
            return

        topics = sorted({entry.topic for entry in EVENT_CATALOG.values()})
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._settings.REDPANDA_BROKERS,
            group_id=self._settings.REDPANDA_BUSINESS_CONSUMER_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await consumer.start()
        logger.info(
            "business_consumer.started",
            topics=topics,
            group_id=self._settings.REDPANDA_BUSINESS_CONSUMER_GROUP_ID,
        )

        try:
            async for message in consumer:
                if not self._running:
                    break
                await self._process_message(message.value)
        finally:
            await consumer.stop()
            logger.info("business_consumer.stopped")

    async def _process_message(self, raw: bytes) -> None:
        try:
            data = json.loads(raw.decode("utf-8"))
            envelope = DomainEventEnvelopeV1.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            logger.warning("business_consumer.invalid_envelope", error=str(exc))
            return

        group_id = self._settings.REDPANDA_BUSINESS_CONSUMER_GROUP_ID

        async with AsyncSessionFactory() as session:
            async with session.begin():
                inbox = DomainEventConsumerInboxRepository(session)
                claimed = await inbox.try_claim(
                    event_id=envelope.event_id,
                    consumer_group_id=group_id,
                    event_type=envelope.event_type,
                )
                if not claimed:
                    logger.debug(
                        "business_consumer.duplicate_skipped",
                        event_id=str(envelope.event_id),
                        consumer_group_id=group_id,
                    )
                    return
                await handle_domain_event(session, envelope)

    def stop(self) -> None:
        self._running = False


async def _main() -> None:
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    consumer = DomainEventBusinessConsumer()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, consumer.stop)
        except NotImplementedError:
            pass

    await consumer.run()


if __name__ == "__main__":
    asyncio.run(_main())
