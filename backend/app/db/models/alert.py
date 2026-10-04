"""
Alert ORM model.

Represents a condition-triggered alert for a field or crop within AGRIFLOW-AI.
Alerts are the real-time notification layer of the Phase 13 intelligence
platform — they surface urgent conditions that require operator attention.

Domain hierarchy:
    Farm → Field → Alert  (field-anchored)
                 → Crop   (optional crop-scoped context)
                 → Recommendation (optional: alert derived from a recommendation)

Design decisions:
- Alerts anchor to ``field_id`` as the primary FK — all environmental conditions
  (soil moisture, weather, satellite signals) are fundamentally field-level.
- ``recommendation_id`` is nullable: alerts can be standalone (sensor threshold
  crossing) or derived from a recommendation (disease risk score exceeds threshold).
- ``triggered_at`` is the primary time key — it represents when the condition
  was detected, not when the row was created. This distinction matters for
  retrospective alert analysis and SLA tracking.
- ``is_acknowledged`` / ``acknowledged_at`` implement the alert acknowledgement
  workflow. Once acknowledged, an alert remains in the history for audit purposes.
- This model is intentionally forward-compatible with:
  - Redpanda AlertTriggered domain events (Phase 14)
  - Digital Twin field health state (Phase 15)
  - Temporal alert escalation workflows (Phase 16)
  - Farm Copilot GaaS alert-aware queries (Phase 16)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AlertSeverity, AlertType
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.field import Field
    from app.db.models.recommendation import Recommendation


class Alert(AuditableModel, Base):
    """
    A condition-triggered alert for a field or crop.

    Domain rules (enforced at service layer):
    - field_id must reference an existing Field.
    - crop_id, when provided, must belong to the same Field.
    - recommendation_id, when provided, must belong to the same Field.
    - triggered_at must be timezone-aware and not in the future.
    - expires_at, when supplied, must be after triggered_at.
    """

    __tablename__ = "alerts"

    __table_args__ = (
        Index("ix_alerts_field_id_triggered_at", "field_id", "triggered_at"),
        Index("ix_alerts_field_id_severity", "field_id", "severity"),
        Index("ix_alerts_field_id_is_acknowledged", "field_id", "is_acknowledged"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent field for which this alert was triggered",
    )
    crop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional crop context; set for crop-specific alerts (disease, harvest)",
    )
    recommendation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional: the recommendation that triggered this alert",
    )

    # ── Classification ────────────────────────────────────────────────────────
    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", create_type=False),
        nullable=False,
        comment="Type of condition that triggered this alert",
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", create_type=False),
        nullable=False,
        comment="Urgency level of the alert (INFO | WARNING | HIGH | CRITICAL)",
    )

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short human-readable alert title",
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Detailed alert message describing the condition and recommended response",
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Timezone-aware timestamp when the alert condition was detected",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional expiry timestamp; NULL means the alert remains active until acknowledged",
    )

    # ── Acknowledgement workflow ───────────────────────────────────────────────
    is_acknowledged: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        comment="Whether an operator has acknowledged this alert",
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the alert was acknowledged",
    )

    # ── Source context ────────────────────────────────────────────────────────
    source_metric: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Name of the metric that triggered the alert (e.g. 'soil_moisture_pct')",
    )
    source_value: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=True,
        comment="Actual metric value at the time of triggering",
    )
    threshold_value: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=True,
        comment="Threshold value that was crossed to trigger this alert",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="alerts")
    crop: Mapped[Crop | None] = relationship()
    recommendation: Mapped[Recommendation | None] = relationship()

    def __repr__(self) -> str:
        return (
            f"<Alert id={self.id}"
            f" type={self.alert_type.value}"
            f" severity={self.severity.value}"
            f" field_id={self.field_id}"
            f" acknowledged={self.is_acknowledged}>"
        )
