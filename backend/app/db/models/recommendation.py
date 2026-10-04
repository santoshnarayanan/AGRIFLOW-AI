"""
Recommendation ORM model.

Represents an actionable agricultural recommendation produced by the
AGRIFLOW-AI decision engine. Recommendations are the primary output of the
Phase 13 intelligence layer and the entry point for the operational timeline.

Domain hierarchy:
    Farm → Field → Recommendation  (field-anchored)
                 → Crop            (optional crop-scoped context)

Design decisions:
- Recommendations anchor to ``field_id`` as the primary FK because irrigation,
  disease risk, and harvest timing recommendations are fundamentally per-field
  assessments, not per-crop.  ``crop_id`` is nullable for recommendations that
  require crop-level context (e.g. HARVEST_TIMING, DISEASE_TREATMENT).
- ``status`` lifecycle: PENDING → ACTIVE → ACKNOWLEDGED → SUPERSEDED|EXPIRED|DISMISSED
- ``confidence_score`` in [0, 1] is produced by the decision engine and
  carries data provenance for the AI layer.
- ``engine_version`` enables A/B comparison between recommendation engine
  versions in future MLOps pipelines.
- ``valid_from`` / ``valid_until`` define the temporal validity window so
  stale recommendations can be auto-expired by a scheduled job (Phase 14).
- This model is intentionally forward-compatible with:
  - Redpanda RecommendationCreated domain events (Phase 14)
  - Feature Store consumption (Phase 15)
  - Farm Copilot GaaS tool layer (Phase 16)
  - Temporal workflow-triggered recommendation pipelines (Phase 16)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import RecommendationPriority, RecommendationStatus, RecommendationType
from app.db.base import AuditableModel, Base

if TYPE_CHECKING:
    from app.db.models.crop import Crop
    from app.db.models.field import Field


class Recommendation(AuditableModel, Base):
    """
    An actionable agricultural recommendation for a specific field.

    Domain rules (enforced at service layer):
    - field_id must reference an existing Field.
    - crop_id, when provided, must reference an existing Crop belonging to the same Field.
    - valid_from must not be in the past by more than 7 days (prevents stale pre-dated recs).
    - valid_until, when supplied, must be after valid_from.
    - confidence_score must be in [0.0, 1.0].
    """

    __tablename__ = "recommendations"

    __table_args__ = (
        Index("ix_recommendations_field_id_status", "field_id", "status"),
        Index("ix_recommendations_field_id_type", "field_id", "recommendation_type"),
        Index("ix_recommendations_field_id_valid_from", "field_id", "valid_from"),
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("fields.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent field for which this recommendation applies",
    )
    crop_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Optional crop context; required for HARVEST_TIMING and DISEASE_TREATMENT types",
    )

    # ── Classification ────────────────────────────────────────────────────────
    recommendation_type: Mapped[RecommendationType] = mapped_column(
        Enum(RecommendationType, name="recommendation_type", create_type=False),
        nullable=False,
        comment="Category of the recommendation (IRRIGATION, DISEASE_TREATMENT, etc.)",
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        Enum(RecommendationStatus, name="recommendation_status", create_type=False),
        nullable=False,
        server_default=RecommendationStatus.PENDING.value,
        comment="Lifecycle state of the recommendation",
    )
    priority: Mapped[RecommendationPriority] = mapped_column(
        Enum(RecommendationPriority, name="recommendation_priority", create_type=False),
        nullable=False,
        server_default=RecommendationPriority.MEDIUM.value,
        comment="Urgency level — maps to Alert severity when an alert is derived",
    )

    # ── Content ───────────────────────────────────────────────────────────────
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Short human-readable title of the recommendation",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed context and rationale for the recommendation",
    )
    recommended_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Specific action the operator should take",
    )

    # ── Quantification ────────────────────────────────────────────────────────
    recommended_value: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=4),
        nullable=True,
        comment="Numeric magnitude of the recommended action (e.g. water volume, kg/ha)",
    )
    recommended_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Unit for recommended_value (e.g. 'liters', 'kg/ha', 'hours')",
    )

    # ── AI / Engine provenance ────────────────────────────────────────────────
    confidence_score: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=4, scale=3),
        nullable=True,
        comment="Engine confidence in [0.000, 1.000]; used for AI feature quality weighting",
    )
    evidence_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable summary of the data signals that drove this recommendation",
    )
    engine_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Version identifier of the recommendation engine (e.g. 'deterministic-v1.0')",
    )

    # ── Validity window ───────────────────────────────────────────────────────
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Start of the recommendation validity window (timezone-aware)",
    )
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="End of the recommendation validity window; NULL means open-ended",
    )

    # ── Workflow ──────────────────────────────────────────────────────────────
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the recommendation was acknowledged by an operator",
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Operator free-text notes on actions taken or reasons for dismissal",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    field: Mapped[Field] = relationship(back_populates="recommendations")
    crop: Mapped[Crop | None] = relationship(back_populates="recommendations")

    def __repr__(self) -> str:
        return (
            f"<Recommendation id={self.id}"
            f" type={self.recommendation_type.value}"
            f" status={self.status.value}"
            f" field_id={self.field_id}>"
        )
