"""enable timescaledb extension

Revision ID: f1e2d3c4b5a6
Revises: a1b2c3d4e5f6
Create Date: 2026-06-29

Phase 12 — Step 1D: TimescaleDB Extension Enablement

Purpose
-------
Activate the TimescaleDB extension in the ``agriflow`` database.
The extension binaries were introduced in Step 1C when the database image
was migrated to ``timescale/timescaledb:2.28.1-pg17``.  This migration
makes the extension active and version-controlled via Alembic.

Governance
----------
Approved under P12-D004 (Decision Register v1.1):
  - Extension enablement strategy: forward Alembic migration
  - Upgrade DDL:   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
  - Downgrade DDL: DROP EXTENSION IF EXISTS timescaledb CASCADE;

Scope Constraints
-----------------
This migration ONLY enables the extension.  The following are explicitly
OUT OF SCOPE and must NOT be added here:
  - Hypertable creation (deferred to Step 1E, requires Architecture ADR)
  - continuous_agg / compression / retention policies
  - Modification of any existing table, index, constraint, or enum
  - Application-layer changes (API / Service / Repository / Schema)

Downgrade Governance
--------------------
The downgrade function satisfies Alembic migration reversibility.

Permitted use:  development environments BEFORE any hypertables exist
                (i.e., before Phase 12 Step 1E).

After Step 1E introduces hypertables, ``DROP EXTENSION ... CASCADE`` is
destructive (it removes all hypertable metadata and chunks).  The approved
rollback procedure at that point is Tier 2 pg_dump restore per P12-D005.

References
----------
- PHASE12_DECISION_REGISTER.md  — P12-D004, P12-D005
- PHASE12_STEP1A_INFRASTRUCTURE_ASSESSMENT.md  — §2.3, §8
- PHASE12_STEP1B_TIMESCALEDB_INFRASTRUCTURE_PLAN.md  — §7.1.1
- PHASE12_STEP1C_IMPLEMENTATION_REPORT.md  — §8, §11
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f1e2d3c4b5a6"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Enable the TimescaleDB extension in the agriflow database.

    IF NOT EXISTS prevents failure on environments where the extension is
    already present (e.g. a shared dev database that was set up manually).
    CASCADE enables the timescaledb_toolkit dependency if it is available
    in the image; it is a no-op if the toolkit is absent.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")


def downgrade() -> None:
    """Remove the TimescaleDB extension.

    GOVERNANCE: This downgrade is permitted only in development environments
    BEFORE any hypertables have been created (before Step 1E).

    After Step 1E introduces hypertables, executing this downgrade would
    CASCADE-drop all hypertable metadata and chunks.  The approved rollback
    path post-Step-1E is Tier 2 pg_dump restore per P12-D005 — NOT this
    downgrade function.

    IF EXISTS prevents failure on environments where the extension was not
    installed by this migration (e.g. partial state during development).
    """
    op.execute("DROP EXTENSION IF EXISTS timescaledb CASCADE;")
