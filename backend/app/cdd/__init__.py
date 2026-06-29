"""
Canonical Development Dataset (CDD) generator package.

Engineering utility for deterministic synthetic agricultural data generation,
validation, persistence, and execution reporting (Steps 2C-B through 2C-C).
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
from app.cdd.execution import (
    CDDExecutionReport,
    DomainVerification,
    VerificationResult,
    execute_cdd_workflow,
    verify_cdd_persistence,
)
from app.cdd.generator import CDDGenerationResult, generate_cdd
from app.cdd.orchestrator import CDDOrchestrator
from app.cdd.persistence import PersistenceResult, persist_cdd_dataset
from app.cdd.statistics import CDDStatistics, build_statistics
from app.cdd.types import CDDDataset, CDDDatasetMetadata
from app.cdd.validation import CDDValidator, ValidationReport

__all__ = [
    "CDDDataset",
    "CDDDatasetMetadata",
    "CDDExecutionReport",
    "CDDGenerationResult",
    "CDDOrchestrator",
    "CDDStatistics",
    "CDDValidator",
    "DomainVerification",
    "PersistenceResult",
    "VerificationResult",
    "build_statistics",
    "execute_cdd_workflow",
    "generate_cdd",
    "persist_cdd_dataset",
    "verify_cdd_persistence",
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
