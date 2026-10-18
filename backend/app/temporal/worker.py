"""
Temporal worker entry point.

Usage:
    python -m app.temporal.worker
"""

from __future__ import annotations

import asyncio

from temporalio.worker import Worker

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.temporal.activities.soil_moisture import (
    create_irrigation_recommendation_for_low_moisture,
    get_latest_soil_moisture,
)
from app.temporal.client import get_temporal_client
from app.temporal.workflows.soil_moisture_alert import SoilMoistureAlertWorkflow

logger = get_logger(__name__)


async def run_worker() -> None:
    settings = get_settings()
    configure_logging(log_level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    client = await get_temporal_client()
    worker = Worker(
        client,
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        workflows=[SoilMoistureAlertWorkflow],
        activities=[
            get_latest_soil_moisture,
            create_irrigation_recommendation_for_low_moisture,
        ],
    )
    logger.info(
        "temporal.worker.starting",
        task_queue=settings.TEMPORAL_TASK_QUEUE,
        host=settings.TEMPORAL_HOST,
    )
    await worker.run()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
