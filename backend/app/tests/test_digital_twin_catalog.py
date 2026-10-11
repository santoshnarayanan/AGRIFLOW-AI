"""Contract tests for Digital Twin catalog."""

from app.digital_twin.catalog import TWIN_STATE_SECTIONS
from app.digital_twin.types import DIGITAL_TWIN_STATE_VERSION


def test_twin_catalog_has_core_sections() -> None:
    sections = {entry.section for entry in TWIN_STATE_SECTIONS}
    assert sections == {
        "field",
        "crops",
        "telemetry_latest",
        "operational",
        "features",
        "provenance",
    }


def test_twin_state_version() -> None:
    assert DIGITAL_TWIN_STATE_VERSION == "twin-v1"
