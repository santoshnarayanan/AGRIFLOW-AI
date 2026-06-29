"""
Canonical Development Dataset (CDD) generator package.

Engineering utility for deterministic synthetic agricultural data generation.
No database writes or CLI execution in Step 2C-B/2C-B enhancement.
"""

from app.cdd.config import (
    CDD_GENERATOR_VERSION,
    CDD_SEED,
    CDD_VERSION,
    DEFAULT_PROFILE,
    TEMPORAL_END,
    TEMPORAL_START,
)
from app.cdd.manifest import (
    FUTURE_PROFILES,
    expected_total_row_count,
    get_manifest,
    list_future_profiles,
    list_profiles,
    register_profile,
)
from app.cdd.orchestrator import CDDOrchestrator
from app.cdd.types import CDDDataset, CDDDatasetMetadata
from app.cdd.validation import CDDValidator, ValidationReport

__all__ = [
    "CDDDataset",
    "CDDDatasetMetadata",
    "CDDOrchestrator",
    "CDDValidator",
    "CDD_GENERATOR_VERSION",
    "CDD_SEED",
    "CDD_VERSION",
    "DEFAULT_PROFILE",
    "FUTURE_PROFILES",
    "TEMPORAL_END",
    "TEMPORAL_START",
    "ValidationReport",
    "expected_total_row_count",
    "get_manifest",
    "list_future_profiles",
    "list_profiles",
    "register_profile",
]
