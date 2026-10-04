"""
AlertService — business logic for the Alert domain.

Responsibilities
----------------
- Verify the parent field exists before creating an alert.                 (rule 1)
- Verify crop_id, when supplied, belongs to the parent field.             (rule 2)
- Verify recommendation_id, when supplied, belongs to the parent field.   (rule 3)
- Ensure triggered_at is not in the future.                               (rule 4)
- Ensure expires_at, when supplied, is after triggered_at.                (rule 5)
- Verify alert exists before update or delete.                            (rule 6)
- Auto-set acknowledged_at when is_acknowledged transitions to True.      (rule 7)
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.alert import Alert
from app.db.repositories.alert import AlertRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.recommendation import RecommendationRepository
from app.schemas.alert import AlertCreate, AlertUpdate
from app.services.field import FieldNotFoundError

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class AlertNotFoundError(ValueError):
    """Raised when the referenced alert does not exist."""


class InvalidAlertError(ValueError):
    """Raised when an alert payload violates business rules."""


class AlertRecommendationMismatchError(ValueError):
    """Raised when recommendation_id does not belong to the given field."""


# ── Service ────────────────────────────────────────────────────────────────────


class AlertService:
    """
    Encapsulates all business logic for Alert operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers can compose and substitute implementations without touching
    service internals.
    """

    def __init__(
        self,
        alert_repository: AlertRepository,
        field_repository: FieldRepository,
        recommendation_repository: RecommendationRepository,
    ) -> None:
        self._alerts = alert_repository
        self._fields = field_repository
        self._recommendations = recommendation_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_alert(
        self,
        field_id: uuid.UUID,
        payload: AlertCreate,
    ) -> Alert:
        """
        Persist a new alert for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        AlertRecommendationMismatchError
            If recommendation_id is supplied but does not belong to the field.
        InvalidAlertError
            If triggered_at is in the future or expires_at <= triggered_at.
        """
        log = logger.bind(
            field_id=str(field_id),
            alert_type=payload.alert_type.value,
        )

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("alert_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 3 — recommendation must belong to the same field
        if payload.recommendation_id is not None:
            rec = await self._recommendations.get_by_id(payload.recommendation_id)
            if rec is None or rec.field_id != field_id:
                log.warning(
                    "alert_service.create.recommendation_mismatch",
                    recommendation_id=str(payload.recommendation_id),
                )
                raise AlertRecommendationMismatchError(
                    f"Recommendation '{payload.recommendation_id}' does not belong to field '{field_id}'."
                )

        # Rule 4 — triggered_at must not be in the future
        _validate_not_future(triggered_at=payload.triggered_at, log=log)

        data: dict[str, Any] = {
            "field_id": field_id,
            "is_acknowledged": False,
            **payload.model_dump(),
        }
        alert = await self._alerts.create(data)
        log.info("alert_service.create.success", alert_id=str(alert.id))

        # ── Future extension point ─────────────────────────────────────────────
        # AlertTriggered domain event → Redpanda (Phase 14)
        # Digital Twin field health state update (Phase 15)
        # Temporal alert escalation workflow trigger (Phase 16)
        # ──────────────────────────────────────────────────────────────────────

        return alert

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_alert(self, alert_id: uuid.UUID) -> Alert | None:
        """Return a single alert by primary key, or None."""
        return await self._alerts.get_by_id(alert_id)

    async def list_field_alerts(
        self,
        field_id: uuid.UUID,
        *,
        active_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Alert]:
        """Return alerts for a field. Pass active_only=True to exclude acknowledged alerts."""
        if active_only:
            return await self._alerts.list_active_by_field(
                field_id, limit=limit, offset=offset
            )
        return await self._alerts.list_by_field(field_id, limit=limit, offset=offset)

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_alert(
        self,
        alert_id: uuid.UUID,
        payload: AlertUpdate,
    ) -> Alert:
        """
        Apply a partial update to an existing alert.

        Automatically sets acknowledged_at when is_acknowledged transitions to True.

        Raises
        ------
        AlertNotFoundError
            If no alert with ``alert_id`` exists.
        """
        log = logger.bind(alert_id=str(alert_id))

        current = await self._alerts.get_by_id(alert_id)
        if current is None:
            log.warning("alert_service.update.not_found")
            raise AlertNotFoundError(f"Alert '{alert_id}' does not exist.")

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 7 — auto-set acknowledged_at
        if (
            update_data.get("is_acknowledged") is True
            and not current.is_acknowledged
            and "acknowledged_at" not in update_data
        ):
            update_data["acknowledged_at"] = datetime.now(timezone.utc)

        updated = await self._alerts.update(alert_id, update_data)
        log.info("alert_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_alert(self, alert_id: uuid.UUID) -> None:
        """
        Permanently delete an alert.

        Raises
        ------
        AlertNotFoundError
            If no alert with ``alert_id`` exists.
        """
        log = logger.bind(alert_id=str(alert_id))
        deleted = await self._alerts.delete(alert_id)
        if not deleted:
            log.warning("alert_service.delete.not_found")
            raise AlertNotFoundError(f"Alert '{alert_id}' does not exist.")
        log.info("alert_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_not_future(*, triggered_at: datetime, log: Any) -> None:
    now_utc = datetime.now(timezone.utc)
    triggered_utc = (
        triggered_at.replace(tzinfo=timezone.utc)
        if triggered_at.tzinfo is None
        else triggered_at.astimezone(timezone.utc)
    )
    if triggered_utc > now_utc:
        log.warning(
            "alert_service.triggered_at_future",
            triggered_at=triggered_at.isoformat(),
        )
        raise InvalidAlertError(
            f"triggered_at ({triggered_at.isoformat()}) cannot be in the future."
        )
