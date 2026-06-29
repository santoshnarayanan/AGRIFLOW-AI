"""
Canonical Development Dataset (CDD) — global configuration constants.

These values identify the dataset specification and anchor the temporal window.
All generators read from here; no hard-coded version or seed values elsewhere.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

# ── Identity ──────────────────────────────────────────────────────────────────
CDD_VERSION: str = "cdd-v1.0.0"
CDD_SEED: int = 42
DEFAULT_PROFILE: str = "cdd-dev"

# Framework code version (distinct from dataset specification version).
# Bump when generator/validation logic changes without a CDD_VERSION bump.
CDD_GENERATOR_VERSION: str = "2c-b.1"

# ── Temporal anchor (America/Chicago per ADR-007-25) ─────────────────────────
CDD_TIMEZONE = ZoneInfo("America/Chicago")

TEMPORAL_START: datetime = datetime(
    2025, 6, 1, 0, 0, 0, tzinfo=CDD_TIMEZONE
)
TEMPORAL_END: datetime = datetime(
    2026, 5, 31, 23, 59, 59, tzinfo=CDD_TIMEZONE
)
CDD_DURATION_DAYS: int = 365
CDD_REFERENCE_NOW: date = date(2026, 5, 31)

# ── Deterministic UUID namespace ─────────────────────────────────────────────
CDD_UUID_NAMESPACE_NAME: str = "agriflow-ai.cdd"
