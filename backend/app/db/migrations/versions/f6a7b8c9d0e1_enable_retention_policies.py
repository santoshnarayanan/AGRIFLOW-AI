"""enable retention policies

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-30

Phase 12 — Step 4B: TimescaleDB Retention Policy Implementation

Purpose
-------
Register add_retention_policy() on five approved raw hypertables and six
approved continuous aggregates, implementing ADR-005 exactly.

Governing Document
------------------
docs/adr/ADR-005-timescaledb-retention-policy-strategy.md (Accepted v1.0)

Decision Register References
-----------------------------
- P12-D011 — Retention Policy Strategy

Rollout Sequence (ADR-005 §5.5)
--------------------------------
Phase 1: sensor_readings raw retention
Phase 2: weather_records, satellite_observations raw retention
Phase 3: irrigation_events, disease_observations raw retention
Phase 4: continuous aggregate retention (six finite-horizon CAs)
Exempt: yield_records (no raw policy); ca_irrigation_monthly,
        ca_yield_seasonal (no CA policy — indefinite per ADR-005 §5.3)

Scope Constraints
-----------------
This migration ONLY implements what is authorised by ADR-005:
  - NO hypertable schema changes
  - NO compression policy changes (ADR-003)
  - NO continuous aggregate refresh policy changes (ADR-004)
  - NO repository / service / API / SQLAlchemy model changes
  - NO Azure Blob Storage archive pipeline (see Archive Integration below)

Yield Records Exemption (ADR-005 §4.4, R-05)
----------------------------------------------
yield_records receives NO add_retention_policy() call. Harvest measurements
are irreplaceable training labels for the Yield Prediction Engine (Phase 14),
financial audit records, and crop insurance evidence. Storage cost is
negligible (tens of rows per field per decade). Any accidental drop would be
a critical data-integrity failure.

Continuous Aggregate Retention (ADR-005 §5.3)
-----------------------------------------------
TimescaleDB 2.28.1 supports add_retention_policy() on continuous aggregate
view names directly (relation accepts hypertable OR continuous aggregate per
TimescaleDB API). Policies are registered on the logical ca_* view names, not
on internal materialization hypertable identifiers.

Six CAs receive finite retention; two are exempt:
  - ca_irrigation_monthly: indefinite — permanent water-use history (~120
    rows/field/decade); negligible storage; ADR-005 §5.3
  - ca_yield_seasonal: indefinite — season-over-season yield features tied to
    exempt yield_records; ADR-005 §5.3

Archive Integration (ADR-005 §5.4 — Deferred)
---------------------------------------------
TODO(AGRIFLOW-ARCHIVE-001): Implement Azure Blob Storage Parquet export pipeline
  before production retention policy activation. ADR-005 mandates
  archive-before-delete (P12-D011, governing principle R-01). This migration
  registers TimescaleDB retention policies only; it does NOT gate drop_chunks
  on successful archive export. Production operators MUST NOT run
  `alembic upgrade head` for this revision in production until the archive
  export job (pre-drop hook) is operational and monitored.

  Future integration point:
    - Trigger: timescaledb_information.jobs policy_retention pre-execution hook
      OR scheduled export job scanning chunks approaching drop_after boundary
    - Target: Azure Blob Storage container (Parquet, field-partitioned paths)
    - Gate: retention drop blocked until archive export confirmed
    - Reference: ADR-005 §8.3 Archive-Before-Delete Workflow

Downgrade Governance
--------------------
remove_retention_policy() on each relation with if_exists => true.
Continuous aggregate and hypertable objects are preserved.
Compression policies (ADR-003) and CA refresh policies (ADR-004) unchanged.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (relation_name, drop_after_interval)
# Values are authoritative per ADR-005 §5.1 — do not modify without ADR amendment.
_RAW_RETENTION_POLICIES: list[tuple[str, str]] = [
    # Phase 1 — sensor (P1 Critical)
    ("sensor_readings", "24 months"),
    # Phase 2 — weather, satellite (P1 Critical)
    ("weather_records", "36 months"),
    ("satellite_observations", "36 months"),
    # Phase 3 — irrigation, disease (P2/P3)
    ("irrigation_events", "7 years"),
    ("disease_observations", "7 years"),
]

# yield_records: EXEMPT — no entry (ADR-005 §5.1 row 6, R-05)

# (continuous_aggregate_view_name, drop_after_interval)
# Values are authoritative per ADR-005 §5.3 — do not modify without ADR amendment.
_CA_RETENTION_POLICIES: list[tuple[str, str]] = [
    # Phase 4 — finite-horizon CA materialisation retention
    ("ca_sensor_hourly", "36 months"),
    ("ca_sensor_daily", "10 years"),
    ("ca_weather_daily", "15 years"),
    ("ca_weather_weekly", "15 years"),
    ("ca_satellite_daily", "10 years"),
    ("ca_disease_weekly", "10 years"),
]

# ca_irrigation_monthly: EXEMPT — indefinite (ADR-005 §5.3 row 6)
# ca_yield_seasonal: EXEMPT — indefinite (ADR-005 §5.3 row 8)


def _add_retention_policy(relation: str, drop_after: str) -> None:
    """Register one TimescaleDB retention policy per ADR-005."""
    op.execute(
        f"""
        SELECT add_retention_policy(
            '{relation}',
            drop_after => INTERVAL '{drop_after}'
        );
        """
    )


def _remove_retention_policy(relation: str) -> None:
    """Remove retention policy before downgrade."""
    op.execute(
        f"SELECT remove_retention_policy('{relation}', if_exists => true);"
    )


def upgrade() -> None:
    """Phase 12 Step 4B: Register raw hypertable and CA retention per ADR-005."""
    # Phases 1–3: raw hypertable retention (five of six hypertables)
    for relation, drop_after in _RAW_RETENTION_POLICIES:
        _add_retention_policy(relation, drop_after)

    # Phase 4: continuous aggregate retention (six of eight CAs)
    for relation, drop_after in _CA_RETENTION_POLICIES:
        _add_retention_policy(relation, drop_after)

    # TODO(AGRIFLOW-ARCHIVE-001): Wire archive-before-delete gate before production
    # activation. See module docstring Archive Integration section.


def downgrade() -> None:
    """Remove all retention policies registered by this migration."""
    # Remove CA policies first (reverse Phase 4 order)
    for relation, _ in reversed(_CA_RETENTION_POLICIES):
        _remove_retention_policy(relation)

    # Remove raw hypertable policies (reverse Phases 1–3 order)
    for relation, _ in reversed(_RAW_RETENTION_POLICIES):
        _remove_retention_policy(relation)
