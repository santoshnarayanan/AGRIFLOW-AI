"""Unit tests for Digital Twin state document assembly."""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from app.db.models.crop import Crop, CropStatus
from app.db.models.field import Field
from app.db.models.field_dashboard_read_model import FieldDashboardReadModel
from app.db.models.sensor_reading import SensorReading
from app.core.enums import SensorType
from app.digital_twin.document import build_field_digital_twin_document
from app.digital_twin.types import DIGITAL_TWIN_STATE_VERSION


def test_build_document_includes_schema_and_telemetry() -> None:
    field_id = uuid.uuid4()
    farm_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    field = Field(
        id=field_id,
        farm_id=farm_id,
        name="North Parcel",
        area_hectares=Decimal("12.5"),
    )
    crop = Crop(
        id=uuid.uuid4(),
        field_id=field_id,
        crop_name="Maize",
        crop_variety=None,
        planting_date=date(2026, 4, 1),
        expected_harvest_date=date(2026, 9, 15),
        status=CropStatus.GROWING,
    )
    reading = SensorReading(
        id=uuid.uuid4(),
        field_id=field_id,
        sensor_type=SensorType.SOIL_MOISTURE,
        sensor_value=Decimal("28.4"),
        unit="%VWC",
        recorded_at=now,
    )
    dashboard = FieldDashboardReadModel(
        id=uuid.uuid4(),
        field_id=field_id,
        farm_id=farm_id,
        field_name="North Parcel",
        open_alerts_count=2,
        critical_alerts_count=1,
        active_recommendations_count=3,
        feature_snapshot_id=None,
        feature_snapshot_as_of=None,
        kpi_payload={"sm_7d_mean": {"value": 27.0, "unit": "percent"}},
        projection_version="v1",
        refreshed_at=now,
    )

    doc = build_field_digital_twin_document(
        field, [crop], [reading], dashboard, synchronized_at=now
    )

    assert doc["schema_version"] == DIGITAL_TWIN_STATE_VERSION
    assert doc["field"]["name"] == "North Parcel"
    assert doc["telemetry_latest"]["SOIL_MOISTURE"]["value"] == 28.4
    assert doc["operational"]["open_alerts_count"] == 2
    assert doc["features"]["sm_7d_mean"]["value"] == 27.0
