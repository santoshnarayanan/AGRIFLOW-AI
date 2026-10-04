"""create alerts table

Phase 13 – Enterprise Decision & Recommendation Platform.

Creates the ``alerts`` table and its PostgreSQL enum types:
  - ``alert_type``
  - ``alert_severity``

Migration chain: follows g1h2i3j4k5l6 (recommendations table).

Revision ID: h2i3j4k5l6m7
Revises: g1h2i3j4k5l6
Create Date: 2026-10-04
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "h2i3j4k5l6m7"
down_revision: str = "g1h2i3j4k5l6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Phase 13 enums — explicit lifecycle per ADR-008-01 pattern ────────────
    alert_type_enum = postgresql.ENUM(
        "SOIL_MOISTURE_LOW",
        "SOIL_MOISTURE_HIGH",
        "DISEASE_RISK_HIGH",
        "DISEASE_OUTBREAK",
        "FROST_RISK",
        "HEAT_STRESS",
        "DROUGHT_STRESS",
        "SENSOR_ANOMALY",
        "IRRIGATION_OVERDUE",
        "HARVEST_WINDOW_OPEN",
        name="alert_type",
    )
    alert_type_enum.create(op.get_bind())

    alert_severity_enum = postgresql.ENUM(
        "INFO",
        "WARNING",
        "HIGH",
        "CRITICAL",
        name="alert_severity",
    )
    alert_severity_enum.create(op.get_bind())

    # ── alerts table ──────────────────────────────────────────────────────────
    op.create_table(
        "alerts",
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
            comment="Parent field for which this alert was triggered",
        ),
        sa.Column(
            "crop_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("crops.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional crop context",
        ),
        sa.Column(
            "recommendation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("recommendations.id", ondelete="SET NULL"),
            nullable=True,
            comment="Optional: the recommendation that triggered this alert",
        ),
        # Classification
        sa.Column(
            "alert_type",
            sa.Enum(
                "SOIL_MOISTURE_LOW",
                "SOIL_MOISTURE_HIGH",
                "DISEASE_RISK_HIGH",
                "DISEASE_OUTBREAK",
                "FROST_RISK",
                "HEAT_STRESS",
                "DROUGHT_STRESS",
                "SENSOR_ANOMALY",
                "IRRIGATION_OVERDUE",
                "HARVEST_WINDOW_OPEN",
                name="alert_type",
                create_type=False,
            ),
            nullable=False,
            comment="Type of condition that triggered this alert",
        ),
        sa.Column(
            "severity",
            sa.Enum(
                "INFO",
                "WARNING",
                "HIGH",
                "CRITICAL",
                name="alert_severity",
                create_type=False,
            ),
            nullable=False,
            comment="Urgency level (INFO | WARNING | HIGH | CRITICAL)",
        ),
        # Content
        sa.Column("title", sa.String(255), nullable=False, comment="Short alert title"),
        sa.Column(
            "message",
            sa.Text,
            nullable=False,
            comment="Detailed alert message",
        ),
        # Timing
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Timezone-aware timestamp when the alert condition was detected",
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Optional expiry; NULL = active until acknowledged",
        ),
        # Acknowledgement workflow
        sa.Column(
            "is_acknowledged",
            sa.Boolean,
            nullable=False,
            server_default="false",
            comment="Whether an operator has acknowledged this alert",
        ),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Timestamp when acknowledged",
        ),
        # Source context
        sa.Column(
            "source_metric",
            sa.String(100),
            nullable=True,
            comment="Name of the metric that triggered the alert",
        ),
        sa.Column(
            "source_value",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
            comment="Actual metric value at triggering",
        ),
        sa.Column(
            "threshold_value",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
            comment="Threshold value that was crossed",
        ),
    )

    # ── Indexes ───────────────────────────────────────────────────────────────
    op.create_index("ix_alerts_field_id", "alerts", ["field_id"])
    op.create_index("ix_alerts_crop_id", "alerts", ["crop_id"])
    op.create_index("ix_alerts_recommendation_id", "alerts", ["recommendation_id"])
    op.create_index(
        "ix_alerts_field_id_triggered_at",
        "alerts",
        ["field_id", "triggered_at"],
    )
    op.create_index(
        "ix_alerts_field_id_severity",
        "alerts",
        ["field_id", "severity"],
    )
    op.create_index(
        "ix_alerts_field_id_is_acknowledged",
        "alerts",
        ["field_id", "is_acknowledged"],
    )


def downgrade() -> None:
    op.drop_index("ix_alerts_field_id_is_acknowledged", table_name="alerts")
    op.drop_index("ix_alerts_field_id_severity", table_name="alerts")
    op.drop_index("ix_alerts_field_id_triggered_at", table_name="alerts")
    op.drop_index("ix_alerts_recommendation_id", table_name="alerts")
    op.drop_index("ix_alerts_crop_id", table_name="alerts")
    op.drop_index("ix_alerts_field_id", table_name="alerts")
    op.drop_table("alerts")

    postgresql.ENUM(name="alert_severity").drop(op.get_bind())
    postgresql.ENUM(name="alert_type").drop(op.get_bind())
