"""Pure functions to assemble the field Digital Twin state document."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.db.models.crop import Crop
from app.db.models.field import Field
from app.db.models.field_dashboard_read_model import FieldDashboardReadModel
from app.db.models.sensor_reading import SensorReading
from app.digital_twin.types import DIGITAL_TWIN_STATE_VERSION


def _decimal_to_json(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def build_field_digital_twin_document(
    field: Field,
    crops: list[Crop],
    latest_sensors: list[SensorReading],
    dashboard: FieldDashboardReadModel | None,
    *,
    synchronized_at: datetime,
) -> dict[str, Any]:
    telemetry: dict[str, Any] = {}
    for reading in latest_sensors:
        telemetry[reading.sensor_type.value] = {
            "value": _decimal_to_json(reading.sensor_value),
            "unit": reading.unit,
            "recorded_at": reading.recorded_at.isoformat(),
            "reading_id": str(reading.id),
        }

    crop_rows = [
        {
            "id": str(crop.id),
            "crop_name": crop.crop_name,
            "crop_variety": crop.crop_variety,
            "status": crop.status.value,
            "planting_date": crop.planting_date.isoformat(),
            "expected_harvest_date": (
                crop.expected_harvest_date.isoformat() if crop.expected_harvest_date else None
            ),
        }
        for crop in crops
    ]

    operational: dict[str, Any] | None = None
    features: dict[str, Any] = {}
    feature_snapshot_id: uuid.UUID | None = None
    dashboard_refreshed_at: datetime | None = None

    if dashboard is not None:
        operational = {
            "open_alerts_count": dashboard.open_alerts_count,
            "critical_alerts_count": dashboard.critical_alerts_count,
            "active_recommendations_count": dashboard.active_recommendations_count,
            "refreshed_at": dashboard.refreshed_at.isoformat(),
        }
        features = dict(dashboard.kpi_payload or {})
        feature_snapshot_id = dashboard.feature_snapshot_id
        dashboard_refreshed_at = dashboard.refreshed_at

    return {
        "schema_version": DIGITAL_TWIN_STATE_VERSION,
        "field": {
            "id": str(field.id),
            "farm_id": str(field.farm_id),
            "name": field.name,
            "area_hectares": _decimal_to_json(field.area_hectares),
            "latitude": _decimal_to_json(field.latitude),
            "longitude": _decimal_to_json(field.longitude),
            "elevation_m": _decimal_to_json(field.elevation_m),
        },
        "crops": crop_rows,
        "telemetry_latest": telemetry,
        "operational": operational,
        "features": features,
        "provenance": {
            "synchronized_at": synchronized_at.isoformat(),
            "dashboard_refreshed_at": (
                dashboard_refreshed_at.isoformat() if dashboard_refreshed_at else None
            ),
            "feature_snapshot_id": str(feature_snapshot_id) if feature_snapshot_id else None,
        },
    }
