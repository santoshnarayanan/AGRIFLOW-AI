"""create recommendations table

Phase 13 – Enterprise Decision & Recommendation Platform.

Creates the ``recommendations`` table and its PostgreSQL enum types:
  - ``recommendation_type``
  - ``recommendation_status``
  - ``recommendation_priority``

Migration chain: follows f6a7b8c9d0e1 (retention policies — Phase 12 HEAD).

Revision ID: g1h2i3j4k5l6
Revises: f6a7b8c9d0e1
Create Date: 2026-10-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g1h2i3j4k5l6"
down_revision: str = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Phase 13 enums — explicit lifecycle per ADR-008-01 pattern ────────────
    recommendation_type_enum = postgresql.ENUM(
        "IRRIGATION",
        "DISEASE_TREATMENT",
        "FERTILIZATION",
        "HARVEST_TIMING",
        "SOIL_AMENDMENT",
        "GENERAL",
        name="recommendation_type",
    )
    recommendation_type_enum.create(op.get_bind())

    recommendation_status_enum = postgresql.ENUM(
        "PENDING",
        "ACTIVE",
        "ACKNOWLEDGED",
        "SUPERSEDED",
        "EXPIRED",
        "DISMISSED",
        name="recommendation_status",
    )
    recommendation_status_enum.create(op.get_bind())

    recommendation_priority_enum = postgresql.ENUM(
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        name="recommendation_priority",
    )
    recommendation_priority_enum.create(op.get_bind())

    # ── recommendations table ─────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        # Identity (AuditableModel)
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID v4 primary key",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Foreign keys
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("fields.id", ondelete="CASCADE"),
            nullable=False,
            comment="Parent field for which this recommendation applies",
        ),
        sa.Column(
            "crop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crops.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional crop context",
        ),
        # Classification
        sa.Column(
            "recommendation_type",
            postgresql.ENUM(
                "IRRIGATION",
                "DISEASE_TREATMENT",
                "FERTILIZATION",
                "HARVEST_TIMING",
                "SOIL_AMENDMENT",
                "GENERAL",
                name="recommendation_type",
                create_type=False,
            ),
            nullable=False,
            comment="Category of the recommendation",
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "ACTIVE",
                "ACKNOWLEDGED",
                "SUPERSEDED",
                "EXPIRED",
                "DISMISSED",
                name="recommendation_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
            comment="Lifecycle state",
        ),
        sa.Column(
            "priority",
            postgresql.ENUM(
                "LOW",
                "MEDIUM",
                "HIGH",
                "CRITICAL",
                name="recommendation_priority",
                create_type=False,
            ),
            nullable=False,
            server_default="MEDIUM",
            comment="Urgency level",
        ),
        # Content
        sa.Column("title", sa.String(255), nullable=False, comment="Short title"),
        sa.Column("description", sa.Text, nullable=True, comment="Detailed rationale"),
        sa.Column(
            "recommended_action",
            sa.Text,
            nullable=False,
            comment="Specific action to take",
        ),
        # Quantification
        sa.Column(
            "recommended_value",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
            comment="Numeric magnitude of the recommended action",
        ),
        sa.Column(
            "recommended_unit",
            sa.String(50),
            nullable=True,
            comment="Unit for recommended_value",
        ),
        # AI / Engine provenance
        sa.Column(
            "confidence_score",
            sa.Numeric(precision=4, scale=3),
            nullable=True,
            comment="Engine confidence in [0.000, 1.000]",
        ),
        sa.Column(
            "evidence_summary",
            sa.Text,
            nullable=True,
            comment="Data signals summary",
        ),
        sa.Column(
            "engine_version",
            sa.String(50),
            nullable=True,
            comment="Version identifier of the recommendation engine",
        ),
        # Validity window
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Start of validity window",
        ),
        sa.Column(
            "valid_until",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="End of validity window; NULL means open-ended",
        ),
        # Workflow
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when acknowledged by an operator",
        ),
        sa.Column("notes", sa.Text, nullable=True, comment="Operator notes"),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index(
        "ix_recommendations_field_id",
        "recommendations",
        ["field_id"],
    )
    op.create_index(
        "ix_recommendations_crop_id",
        "recommendations",
        ["crop_id"],
    )
    op.create_index(
        "ix_recommendations_field_id_status",
        "recommendations",
        ["field_id", "status"],
    )
    op.create_index(
        "ix_recommendations_field_id_type",
        "recommendations",
        ["field_id", "recommendation_type"],
    )
    op.create_index(
        "ix_recommendations_field_id_valid_from",
        "recommendations",
        ["field_id", "valid_from"],
    )


def downgrade() -> None:
    op.drop_index("ix_recommendations_field_id_valid_from", table_name="recommendations")
    op.drop_index("ix_recommendations_field_id_type", table_name="recommendations")
    op.drop_index("ix_recommendations_field_id_status", table_name="recommendations")
    op.drop_index("ix_recommendations_crop_id", table_name="recommendations")
    op.drop_index("ix_recommendations_field_id", table_name="recommendations")
    op.drop_table("recommendations")

    postgresql.ENUM(name="recommendation_priority").drop(op.get_bind())
    postgresql.ENUM(name="recommendation_status").drop(op.get_bind())
    postgresql.ENUM(name="recommendation_type").drop(op.get_bind())
