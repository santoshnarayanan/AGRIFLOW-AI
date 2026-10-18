"""SoilMoistureAlertWorkflow — durable deficit evaluation (Phase 16)."""

from __future__ import annotations

from datetime import timedelta

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from app.temporal.activities.soil_moisture import (
        create_irrigation_recommendation_for_low_moisture,
        get_latest_soil_moisture,
    )


@workflow.defn(name="SoilMoistureAlertWorkflow")
class SoilMoistureAlertWorkflow:
    """
    Wait for persistence, re-check soil moisture, then create irrigation guidance.

    Input dict keys: field_id, sensor_reading_id, sensor_value, threshold_percent,
    persistence_minutes (optional override for tests).
    """

    @workflow.run
    async def run(self, input: dict) -> dict:
        field_id = input["field_id"]
        reading_id = input["sensor_reading_id"]
        threshold = float(input["threshold_percent"])
        persistence_minutes = int(input.get("persistence_minutes", 15))

        await workflow.sleep(timedelta(minutes=persistence_minutes))

        latest = await workflow.execute_activity(
            get_latest_soil_moisture,
            args=[field_id, threshold],
            start_to_close_timeout=timedelta(seconds=60),
        )
        if not latest.get("below_threshold"):
            return {
                "status": "cleared",
                "field_id": field_id,
                "latest": latest,
            }

        created = await workflow.execute_activity(
            create_irrigation_recommendation_for_low_moisture,
            args=[field_id, threshold, reading_id],
            start_to_close_timeout=timedelta(seconds=120),
        )
        return {
            "status": "recommendation_created",
            "field_id": field_id,
            "latest": latest,
            "created": created,
        }
