"""
Outbox relay — publishes pending domain events to Redpanda (Phase 14).

Run as a separate process (same image as the API):

    python -m app.events.relay

Requires ``EVENTS_ENABLED=true`` and ``REDPANDA_ENABLED=true``.
"""

from __future__ import annotations

import asyncio
import json
import signal

from aiokafka import AIOKafkaProducer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.repositories.domain_event_outbox import DomainEventOutboxRepository
from app.db.session import AsyncSessionFactory

logger = get_logger(__name__)


class OutboxRelay:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._running = True

    async def run(self) -> None:
        if not self._settings.EVENTS_ENABLED:
            logger.warning("outbox_relay.events_disabled")
            return
        if not self._settings.REDPANDA_ENABLED:
            logger.warning("outbox_relay.redpanda_disabled")
            return

        producer = AIOKafkaProducer(
            bootstrap_servers=self._settings.REDPANDA_BROKERS,
            client_id=self._settings.REDPANDA_CLIENT_ID,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
        )
        await producer.start()
        logger.info(
            "outbox_relay.started",
            brokers=self._settings.REDPANDA_BROKERS,
            poll_interval=self._settings.OUTBOX_RELAY_POLL_INTERVAL_SECONDS,
        )

        try:
            while self._running:
                await self._publish_batch(producer)
                await asyncio.sleep(self._settings.OUTBOX_RELAY_POLL_INTERVAL_SECONDS)
        finally:
            await producer.stop()
            logger.info("outbox_relay.stopped")

    async def _publish_batch(self, producer: AIOKafkaProducer) -> None:
        async with AsyncSessionFactory() as session:
            async with session.begin():
                repo = DomainEventOutboxRepository(session)
                pending = await repo.list_pending(
                    limit=self._settings.OUTBOX_RELAY_BATCH_SIZE
                )
                for row in pending:
                    try:
                        key = str(row.aggregate_id)
                        await producer.send_and_wait(
                            row.topic,
                            value=row.payload,
                            key=key,
                        )
                        await repo.mark_published(row.id)
                        logger.info(
                            "outbox_relay.published",
                            event_id=str(row.id),
                            topic=row.topic,
                        )
                    except Exception as exc:
                        await repo.mark_failed(row.id, str(exc))
                        logger.error(
                            "outbox_relay.publish_failed",
                            event_id=str(row.id),
                            error=str(exc),
                        )

    def stop(self) -> None:
        self._running = False


async def _main() -> None:
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    relay = OutboxRelay()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, relay.stop)
        except NotImplementedError:
            # Windows
            pass

    await relay.run()


if __name__ == "__main__":
    asyncio.run(_main())
