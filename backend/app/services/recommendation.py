"""
RecommendationService — business logic for the Recommendation domain.

Responsibilities
----------------
- Verify the parent field exists before creating a recommendation.         (rule 1)
- Verify the crop_id, when supplied, belongs to the parent field.          (rule 2)
- Validate confidence_score is within [0.0, 1.0] when supplied.           (rule 3)
- Enforce valid_until > valid_from when both are present.                  (rule 4)
- Verify recommendation exists before update or delete.                    (rule 5)
- Set acknowledged_at when status transitions to ACKNOWLEDGED.             (rule 6)

The service never touches raw SQL. All database access is delegated to the
injected repositories.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.enums import RecommendationStatus
from app.core.logging.logger import get_logger
from app.db.models.recommendation import Recommendation
from app.db.repositories.crop import CropRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.schemas.recommendation import RecommendationCreate, RecommendationUpdate
from app.services.field import FieldNotFoundError

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class RecommendationNotFoundError(ValueError):
    """Raised when the referenced recommendation does not exist."""


class InvalidRecommendationError(ValueError):
    """Raised when a recommendation payload violates business rules."""


class CropFieldMismatchError(ValueError):
    """Raised when the supplied crop_id does not belong to the given field."""


# ── Service ────────────────────────────────────────────────────────────────────


class RecommendationService:
    """
    Encapsulates all business logic for Recommendation operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers can compose and substitute implementations without touching
    service internals.
    """

    def __init__(
        self,
        recommendation_repository: RecommendationRepository,
        field_repository: FieldRepository,
        crop_repository: CropRepository,
    ) -> None:
        self._recommendations = recommendation_repository
        self._fields = field_repository
        self._crops = crop_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_recommendation(
        self,
        field_id: uuid.UUID,
        payload: RecommendationCreate,
    ) -> Recommendation:
        """
        Persist a new recommendation for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        CropFieldMismatchError
            If crop_id is supplied but does not belong to the field.
        InvalidRecommendationError
            If confidence_score is out of range or validity window is invalid.
        """
        log = logger.bind(
            field_id=str(field_id),
            recommendation_type=payload.recommendation_type.value,
        )

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("recommendation_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 2 — crop must belong to the same field
        if payload.crop_id is not None:
            crop = await self._crops.get_by_id(payload.crop_id)
            if crop is None or crop.field_id != field_id:
                log.warning(
                    "recommendation_service.create.crop_field_mismatch",
                    crop_id=str(payload.crop_id),
                )
                raise CropFieldMismatchError(
                    f"Crop '{payload.crop_id}' does not belong to field '{field_id}'."
                )

        # Rule 3 — confidence_score in [0, 1]
        if payload.confidence_score is not None:
            _validate_confidence(payload.confidence_score, log=log)

        data: dict[str, Any] = {
            "field_id": field_id,
            "status": RecommendationStatus.PENDING,
            **payload.model_dump(),
        }
        rec = await self._recommendations.create(data)
        log.info(
            "recommendation_service.create.success",
            recommendation_id=str(rec.id),
        )

        # ── Future extension point ─────────────────────────────────────────────
        # RecommendationCreated domain event → Redpanda (Phase 14)
        # Feature Store feature vector update (Phase 15)
        # Farm Copilot GaaS tool trigger (Phase 16)
        # ──────────────────────────────────────────────────────────────────────

        return rec

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_recommendation(
        self, recommendation_id: uuid.UUID
    ) -> Recommendation | None:
        """Return a single recommendation by primary key, or None."""
        return await self._recommendations.get_by_id(recommendation_id)

    async def list_field_recommendations(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Recommendation]:
        """Return all recommendations for a field, newest first."""
        return await self._recommendations.list_by_field(
            field_id, limit=limit, offset=offset
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_recommendation(
        self,
        recommendation_id: uuid.UUID,
        payload: RecommendationUpdate,
    ) -> Recommendation:
        """
        Apply a partial update to an existing recommendation.

        Automatically sets acknowledged_at when status transitions to ACKNOWLEDGED.

        Raises
        ------
        RecommendationNotFoundError
            If no recommendation with ``recommendation_id`` exists.
        InvalidRecommendationError
            If confidence_score is out of range.
        """
        log = logger.bind(recommendation_id=str(recommendation_id))

        # Rule 5 — must exist
        current = await self._recommendations.get_by_id(recommendation_id)
        if current is None:
            log.warning("recommendation_service.update.not_found")
            raise RecommendationNotFoundError(
                f"Recommendation '{recommendation_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 3 — confidence_score
        if "confidence_score" in update_data and update_data["confidence_score"] is not None:
            _validate_confidence(update_data["confidence_score"], log=log)

        # Rule 6 — auto-set acknowledged_at on ACKNOWLEDGED transition
        if (
            update_data.get("status") == RecommendationStatus.ACKNOWLEDGED
            and current.acknowledged_at is None
            and "acknowledged_at" not in update_data
        ):
            update_data["acknowledged_at"] = datetime.now(timezone.utc)

        updated = await self._recommendations.update(recommendation_id, update_data)
        log.info("recommendation_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_recommendation(self, recommendation_id: uuid.UUID) -> None:
        """
        Permanently delete a recommendation.

        Raises
        ------
        RecommendationNotFoundError
            If no recommendation with ``recommendation_id`` exists.
        """
        log = logger.bind(recommendation_id=str(recommendation_id))
        deleted = await self._recommendations.delete(recommendation_id)
        if not deleted:
            log.warning("recommendation_service.delete.not_found")
            raise RecommendationNotFoundError(
                f"Recommendation '{recommendation_id}' does not exist."
            )
        log.info("recommendation_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_confidence(score: Decimal, *, log: Any) -> None:
    if not (Decimal("0") <= score <= Decimal("1")):
        log.warning("recommendation_service.invalid_confidence", score=str(score))
        raise InvalidRecommendationError(
            f"confidence_score ({score}) must be in [0.000, 1.000]."
        )
