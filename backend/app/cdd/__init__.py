"""
Canonical Development Dataset (CDD) generator package.

Engineering utility for deterministic synthetic agricultural data generation.
No database writes or CLI execution in Step 2C-B.
"""

from app.cdd.config import (
    CDD_SEED,
    CDD_VERSION,
    DEFAULT_PROFILE,
    TEMPORAL_END,
    TEMPORAL_START,
)
from app.cdd.manifest import get_manifest, list_profiles
from app.cdd.orchestrator import CDDOrchestrator
from app.cdd.types import CDDDataset

__all__ = [
    "CDDDataset",
    "CDDOrchestrator",
    "CDD_SEED",
    "CDD_VERSION",
    "DEFAULT_PROFILE",
    "TEMPORAL_END",
    "TEMPORAL_START",
    "get_manifest",
    "list_profiles",
]
