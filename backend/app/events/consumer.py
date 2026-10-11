"""
Development domain-event consumer (Phase 14).

Subscribes to all catalog topics and logs envelopes — validates the relay path.

    python -m app.events.consumer
"""

from __future__ import annotations

import asyncio
import json
import signal

from aiokafka import AIOKafkaConsumer

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.events.catalog import EVENT_CATALOG

logger = get_logger(__name__)


class DomainEventAuditConsumer:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = True

    async def run(self) -> None:
        if not self._settings.REDPANDA_ENABLED:
            logger.warning("domain_event_consumer.redpanda_disabled")
            return

        topics = sorted({entry.topic for entry in EVENT_CATALOG.values()})
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._settings.REDPANDA_BROKERS,
            group_id=self._settings.REDPANDA_CONSUMER_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await consumer.start()
        logger.info("domain_event_consumer.started", topics=topics)

        try:
            async for message in consumer:
                if not self._running:
                    break
                try:
                    payload = json.loads(message.value.decode("utf-8"))
                    logger.info(
                        "domain_event_consumer.received",
                        topic=message.topic,
                        event_type=payload.get("event_type"),
                        event_id=payload.get("event_id"),
                        aggregate_id=payload.get("aggregate_id"),
                    )
                except json.JSONDecodeError:
                    logger.warning(
                        "domain_event_consumer.invalid_json",
                        topic=message.topic,
                    )
        finally:
            await consumer.stop()
            logger.info("domain_event_consumer.stopped")

    def stop(self) -> None:
        self._running = False


async def _main() -> None:
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    consumer = DomainEventAuditConsumer()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, consumer.stop)
        except NotImplementedError:
            pass

    await consumer.run()


if __name__ == "__main__":
    asyncio.run(_main())
