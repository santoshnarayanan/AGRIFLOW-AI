"""Temporal workflow unit tests (Phase 16)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from temporalio import activity
from temporalio.testing import WorkflowEnvironment
from temporalio.worker import Worker

from app.temporal.workflows.soil_moisture_alert import SoilMoistureAlertWorkflow


@activity.defn(name="get_latest_soil_moisture")
async def _mock_get_latest_soil_moisture(field_id: str, threshold_percent: float) -> dict:
    return {
        "field_id": field_id,
        "sensor_value": 42.0,
        "unit": "%",
        "recorded_at": "2026-06-01T12:00:00+00:00",
        "below_threshold": False,
    }


@activity.defn(name="create_irrigation_recommendation_for_low_moisture")
async def _mock_create_recommendation(
    field_id: str, threshold_percent: float, trigger_reading_id: str
) -> dict:
    raise AssertionError("should not run when moisture recovered")


@pytest.mark.asyncio
async def test_soil_moisture_workflow_clears_when_moisture_recovered() -> None:
    async with await WorkflowEnvironment.start_time_skipping() as env:
        async with Worker(
            env.client,
            task_queue="test-alerts",
            workflows=[SoilMoistureAlertWorkflow],
            activities=[_mock_get_latest_soil_moisture, _mock_create_recommendation],
        ):
            result = await env.client.execute_workflow(
                SoilMoistureAlertWorkflow.run,
                {
                    "field_id": "00000000-0000-4000-8000-000000000001",
                    "sensor_reading_id": "00000000-0000-4000-8000-000000000002",
                    "sensor_value": 10.0,
                    "threshold_percent": 20.0,
                    "persistence_minutes": 0,
                },
                id="test-soil-moisture-cleared",
                task_queue="test-alerts",
                execution_timeout=timedelta(seconds=30),
            )
    assert result["status"] == "cleared"
