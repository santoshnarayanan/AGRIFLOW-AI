"""enable hypertable compression policies

Revision ID: d4f5e6a7b8c9
Revises: c9d8e7f6a5b4
Create Date: 2026-06-29

Phase 12 — Step 2B: TimescaleDB Compression Implementation

Purpose
-------
Enable TimescaleDB native columnar compression and add_compression_policy()
on all six approved hypertables, implementing ADR-003 exactly.

Governing Document
------------------
docs/adr/ADR-003-timescaledb-compression-policy-strategy.md (Approved v1.1)

Decision Register References
-----------------------------
- P12-D010 — Compression Policy Strategy

Rollout Sequence (ADR-003 §4)
------------------------------
Phase 1: sensor_readings, weather_records, satellite_observations
Phase 2: irrigation_events, yield_records
Phase 3: disease_observations

Scope Constraints
-----------------
This migration ONLY implements what is authorised by ADR-003:
  - NO continuous aggregates
  - NO retention policies
  - NO repository changes
  - NO service changes
  - NO API changes
  - NO SQLAlchemy model changes

Downgrade Governance
--------------------
remove_compression_policy() then disable compression on each hypertable.
If compressed chunks exist, decompress_chunk() must run before downgrade.
On empty hypertables (current dev state), no chunks exist — downgrade is safe.
For non-empty environments with compressed chunks, use Tier 2 pg_dump restore.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d4f5e6a7b8c9"
down_revision: Union[str, None] = "c9d8e7f6a5b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (table_name, segmentby, orderby, compress_after_interval)
# Values are authoritative per ADR-003 §4 — do not modify without ADR amendment.
_COMPRESSION_POLICIES: list[tuple[str, str, str, str]] = [
    # Phase 1 — P1 Critical
    ("sensor_readings", "field_id, sensor_type", "recorded_at DESC", "7 days"),
    ("weather_records", "field_id", "recorded_at DESC", "7 days"),
    (
        "satellite_observations",
        "field_id, spectral_index",
        "observed_at DESC",
        "14 days",
    ),
    # Phase 2 — P2 High
    ("irrigation_events", "field_id", "started_at DESC", "60 days"),
    ("yield_records", "crop_id", "recorded_at DESC", "180 days"),
    # Phase 3 — P3 Standard
    ("disease_observations", "crop_id", "observed_at DESC", "60 days"),
]


def _enable_compression(
    table: str, segmentby: str, orderby: str, compress_after: str
) -> None:
    """Enable compression settings and add policy for one hypertable."""
    op.execute(
        f"""
        ALTER TABLE {table} SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = '{segmentby}',
            timescaledb.compress_orderby = '{orderby}'
        );
        """
    )
    op.execute(
        f"SELECT add_compression_policy('{table}', INTERVAL '{compress_after}');"
    )


def _disable_compression(table: str) -> None:
    """Remove compression policy and disable compression for one hypertable."""
    # Decompress any compressed chunks before removing policy (safe no-op if none).
    op.execute(
        f"""
        SELECT decompress_chunk(c, if_compressed => true)
        FROM show_chunks('{table}') AS c;
        """
    )
    op.execute(f"SELECT remove_compression_policy('{table}', if_exists => true);")
    op.execute(f"ALTER TABLE {table} SET (timescaledb.compress = false);")


def upgrade() -> None:
    """Phase 12 Step 2B: Enable compression on all six hypertables per ADR-003."""
    for table, segmentby, orderby, compress_after in _COMPRESSION_POLICIES:
        _enable_compression(table, segmentby, orderby, compress_after)


def downgrade() -> None:
    """Revert compression policies and disable compression on all six hypertables."""
    for table, _, _, _ in reversed(_COMPRESSION_POLICIES):
        _disable_compression(table)
