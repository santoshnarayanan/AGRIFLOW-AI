"""Event catalog and schema version contract tests (Phase 14)."""

from app.events.catalog import EVENT_CATALOG
from app.events.types import DomainEventType
from app.ml.registry import ML_ENGINE_REGISTRY
from app.ml.types import MLEngineId


def test_event_catalog_covers_all_domain_event_types() -> None:
    assert set(EVENT_CATALOG.keys()) == set(DomainEventType)


def test_event_catalog_schema_versions_are_semver_like() -> None:
    for entry in EVENT_CATALOG.values():
        parts = entry.schema_version.split(".")
        assert len(parts) >= 2
        assert all(part.isdigit() for part in parts[:2])


def test_ml_engine_registry_lists_three_stubs() -> None:
    assert set(ML_ENGINE_REGISTRY.keys()) == set(MLEngineId)
