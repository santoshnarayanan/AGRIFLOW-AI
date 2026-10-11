"""Digital Twin state document catalog for integrators."""

from __future__ import annotations

from dataclasses import dataclass

from app.digital_twin.types import DIGITAL_TWIN_STATE_VERSION


@dataclass(frozen=True, slots=True)
class TwinStateSectionCatalogEntry:
    section: str
    description: str
    source: str


TWIN_STATE_SECTIONS: tuple[TwinStateSectionCatalogEntry, ...] = (
    TwinStateSectionCatalogEntry(
        section="field",
        description="Static field identity and geospatial attributes.",
        source="fields",
    ),
    TwinStateSectionCatalogEntry(
        section="crops",
        description="Active crop cycles on the field.",
        source="crops",
    ),
    TwinStateSectionCatalogEntry(
        section="telemetry_latest",
        description="Most recent sensor reading per SensorType.",
        source="sensor_readings",
    ),
    TwinStateSectionCatalogEntry(
        section="operational",
        description="Alert and recommendation KPIs from CQRS dashboard read model.",
        source="field_dashboard_read_models",
    ),
    TwinStateSectionCatalogEntry(
        section="features",
        description="Highlighted agronomic features from latest Feature Store snapshot.",
        source="field_feature_snapshots",
    ),
    TwinStateSectionCatalogEntry(
        section="provenance",
        description="Synchronization timestamps and upstream snapshot references.",
        source="digital_twin_synchronize",
    ),
)


def state_schema_version() -> str:
    return DIGITAL_TWIN_STATE_VERSION
