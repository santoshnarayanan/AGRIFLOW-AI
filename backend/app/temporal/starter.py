"""Workflow starters invoked from the API service layer."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.core.config import get_settings
from app.core.enums import SensorType
from app.core.logging.logger import get_logger
from app.db.models.sensor_reading import SensorReading
from app.temporal.workflows.soil_moisture_alert import SoilMoistureAlertWorkflow

logger = get_logger(__name__)


class SoilMoistureWorkflowStarter(ABC):
    @abstractmethod
    async def maybe_start_for_reading(self, reading: SensorReading) -> None:
        """Start a durability workflow when a low soil moisture reading is ingested."""


class NoOpSoilMoistureWorkflowStarter(SoilMoistureWorkflowStarter):
    async def maybe_start_for_reading(self, reading: SensorReading) -> None:
        return None


class TemporalSoilMoistureWorkflowStarter(SoilMoistureWorkflowStarter):
    def __init__(self) -> None:
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from app.temporal.client import get_temporal_client

            self._client = await get_temporal_client()
        return self._client

    async def maybe_start_for_reading(self, reading: SensorReading) -> None:
        settings = get_settings()
        if reading.sensor_type != SensorType.SOIL_MOISTURE:
            return
        if float(reading.sensor_value) >= settings.SOIL_MOISTURE_LOW_THRESHOLD_PERCENT:
            return

        client = await self._get_client()
        workflow_id = f"soil-moisture-alert-{reading.field_id}-{reading.id}"
        recorded_at: datetime = reading.recorded_at
        from temporalio.service import RPCError

        try:
            await client.start_workflow(
                SoilMoistureAlertWorkflow.run,
                {
                    "field_id": str(reading.field_id),
                    "sensor_reading_id": str(reading.id),
                    "sensor_value": float(reading.sensor_value),
                    "threshold_percent": settings.SOIL_MOISTURE_LOW_THRESHOLD_PERCENT,
                    "persistence_minutes": settings.TEMPORAL_SOIL_MOISTURE_PERSISTENCE_MINUTES,
                },
                id=workflow_id,
                task_queue=settings.TEMPORAL_TASK_QUEUE,
            )
            logger.info(
                "temporal.workflow.started",
                workflow_id=workflow_id,
                field_id=str(reading.field_id),
            )
        except RPCError as exc:
            if "already started" in str(exc).lower() or "already exists" in str(exc).lower():
                logger.debug(
                    "temporal.workflow.duplicate",
                    workflow_id=workflow_id,
                )
                return
            raise


_starter: SoilMoistureWorkflowStarter | None = None


def get_soil_moisture_workflow_starter() -> SoilMoistureWorkflowStarter:
    global _starter
    if _starter is not None:
        return _starter
    settings = get_settings()
    if settings.TEMPORAL_ENABLED:
        _starter = TemporalSoilMoistureWorkflowStarter()
    else:
        _starter = NoOpSoilMoistureWorkflowStarter()
    return _starter
