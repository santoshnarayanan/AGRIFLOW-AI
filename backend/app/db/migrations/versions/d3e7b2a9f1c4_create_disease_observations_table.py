"""create disease_observations table

Revision ID: d3e7b2a9f1c4
Revises: b7e2a9f4c8d3
Create Date: 2026-06-23 18:00:00.000000

Creates the disease_observations table — Phase 10 of AGRIFLOW-AI.
DiseaseObservation is a grandchild domain:

    Farm → Field → Crop → DiseaseObservation

Like YieldRecord, DiseaseObservation anchors on Crop because disease pressure
is a per-crop-cycle measurement.  ``field_id`` is denormalized onto the table
(ADR-009-02) to enable field-scoped queries without a JOIN through ``crops``.

Notable DDL decisions
---------------------
- Two named PostgreSQL ENUM types are created before the table:
    ``disease_severity``  — severity classification (LOW, MEDIUM, HIGH, CRITICAL)
    ``diagnosis_method``  — identification method (VISUAL_INSPECTION, LAB_ANALYSIS, …)
  Both are dropped explicitly in downgrade() because PostgreSQL does NOT
  automatically drop named enum types when the owning table is removed.
- postgresql.ENUM with create_type=False is used so that op.create_table()
  does not emit a second CREATE TYPE.  The type lifecycle is owned entirely
  by the .create() / .drop() calls — see migration b7e2a9f4c8d3 for the
  full rationale (sa.Enum._copy() does not forward create_type=False in
  SQLAlchemy 2.0.x).
- ``observed_at`` is the primary time key: TIMESTAMPTZ NOT NULL, individually
  indexed, and included in the compound index with crop_id.  It is the
  partition key for a future TimescaleDB hypertable promotion.
- Two FK constraints with ON DELETE CASCADE are declared:
    fk_disease_observations_crop_id  — primary domain anchor
    fk_disease_observations_field_id — denormalized path for field-scoped queries
  Both cascade on delete so disease observations are removed when either the
  crop cycle or the field is deleted.
- Five indexes cover the dominant access patterns:
    1. ix_disease_observations_crop_id             — "all observations for a crop cycle"
    2. ix_disease_observations_field_id            — "all observations for a field (direct)"
    3. ix_disease_observations_observed_at         — "observations in a time window"
    4. ix_disease_observations_disease_name        — "filter by disease name"
    5. ix_disease_observations_severity            — "filter by severity"
    6. ix_disease_observations_crop_id_observed_at — "crop observations in time order"
  Index 6 is the primary compound access pattern for disease history queries
  and the Phase 13 Disease Risk Scoring Engine feature pipeline.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d3e7b2a9f1c4"
down_revision: Union[str, None] = "b7e2a9f4c8d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# postgresql.ENUM (not sa.Enum) is used here intentionally.
# sa.Enum._copy() — called internally by op.create_table() when the type is
# cloned into the temporary Table object — does not forward create_type=False
# in SQLAlchemy 2.0.x, causing a DuplicateObjectError on fresh databases.
# postgresql.ENUM preserves create_type=False through _set_table() and _copy()
# so op.create_table() emits no DDL for these types.
disease_severity_enum = postgresql.ENUM(
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
    name="disease_severity",
    create_type=False,
)

diagnosis_method_enum = postgresql.ENUM(
    "VISUAL_INSPECTION",
    "LAB_ANALYSIS",
    "IMAGE_AI",
    "AGRONOMIST",
    "SENSOR_DETECTED",
    name="diagnosis_method",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create PostgreSQL ENUM types ─────────────────────────────────────
    # Must exist before the table that references them.  create_type=False on
    # the enum objects above ensures op.create_table() does not emit a second
    # CREATE TYPE.
    disease_severity_enum.create(op.get_bind(), checkfirst=True)
    diagnosis_method_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Create the disease_observations table ────────────────────────────
    op.create_table(
        "disease_observations",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Foreign keys ──────────────────────────────────────────────────────
        sa.Column(
            "crop_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment=(
                "Crop cycle this disease observation belongs to; "
                "primary domain anchor — disease pressure is per crop cycle"
            ),
        ),
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment=(
                "Denormalized field FK (ADR-009-02); "
                "enables direct field-scoped queries without a JOIN through crops"
            ),
        ),
        # ── Observation timestamp ─────────────────────────────────────────────
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment=(
                "Timezone-aware timestamp when this disease was observed; "
                "serves as the primary time key and TimescaleDB partition key"
            ),
        ),
        # ── Disease identification ────────────────────────────────────────────
        sa.Column(
            "disease_name",
            sa.String(255),
            nullable=False,
            comment="Free-text disease name, e.g. 'Rust', 'Powdery Mildew', 'Late Blight'",
        ),
        sa.Column(
            "severity",
            disease_severity_enum,
            nullable=False,
            comment="Severity classification of the observed disease pressure",
        ),
        sa.Column(
            "affected_area_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment="Percentage of crop area affected by the disease; valid range [0, 100]",
        ),
        # ── Diagnosis classification ──────────────────────────────────────────
        sa.Column(
            "diagnosis_method",
            diagnosis_method_enum,
            nullable=False,
            comment="Method by which the disease was identified or confirmed",
        ),
        # ── Treatment and metadata ────────────────────────────────────────────
        sa.Column(
            "treatment_applied",
            sa.Text(),
            nullable=True,
            comment="Treatment applied in response to the observation, e.g. fungicide application",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Operator free-text annotations, e.g. follow-up inspection plans",
        ),
        # ── Audit timestamps (server-side) ────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row creation timestamp (set by PostgreSQL)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row last-updated timestamp (set by PostgreSQL)",
        ),
        # ── Table-level constraints ───────────────────────────────────────────
        sa.ForeignKeyConstraint(
            ["crop_id"],
            ["crops.id"],
            name="fk_disease_observations_crop_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
            name="fk_disease_observations_field_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_disease_observations"),
    )

    # ── 3. Indexes ────────────────────────────────────────────────────────────
    # Five individual indexes support single-predicate queries.
    # The compound index is the primary access pattern for crop disease history
    # and the Phase 13 AI feature pipeline.
    op.create_index(
        op.f("ix_disease_observations_crop_id"),
        "disease_observations",
        ["crop_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disease_observations_field_id"),
        "disease_observations",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disease_observations_observed_at"),
        "disease_observations",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disease_observations_disease_name"),
        "disease_observations",
        ["disease_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_disease_observations_severity"),
        "disease_observations",
        ["severity"],
        unique=False,
    )
    op.create_index(
        "ix_disease_observations_crop_id_observed_at",
        "disease_observations",
        ["crop_id", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: compound index → individual indexes → table → enum types.
    # ForeignKeyConstraint and PrimaryKeyConstraint are dropped automatically
    # when the table is removed.

    # ── Compound index ────────────────────────────────────────────────────────
    op.drop_index(
        "ix_disease_observations_crop_id_observed_at",
        table_name="disease_observations",
    )

    # ── Individual indexes ────────────────────────────────────────────────────
    op.drop_index(
        op.f("ix_disease_observations_severity"),
        table_name="disease_observations",
    )
    op.drop_index(
        op.f("ix_disease_observations_disease_name"),
        table_name="disease_observations",
    )
    op.drop_index(
        op.f("ix_disease_observations_observed_at"),
        table_name="disease_observations",
    )
    op.drop_index(
        op.f("ix_disease_observations_field_id"),
        table_name="disease_observations",
    )
    op.drop_index(
        op.f("ix_disease_observations_crop_id"),
        table_name="disease_observations",
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.drop_table("disease_observations")

    # ── Enum types ────────────────────────────────────────────────────────────
    # PostgreSQL retains named enum types after the owning table is dropped;
    # explicit removal is required to leave no orphan types in the schema.
    # .drop() is symmetric with .create() in upgrade().
    diagnosis_method_enum.drop(op.get_bind(), checkfirst=False)
    disease_severity_enum.drop(op.get_bind(), checkfirst=False)
