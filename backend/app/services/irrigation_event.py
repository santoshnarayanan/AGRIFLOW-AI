"""
IrrigationEventService — business logic for the IrrigationEvent domain.

Responsibilities
----------------
- Verify the parent field exists before creating an irrigation event.     (rule 1)
- Ensure started_at is not in the future.                                 (rule 2)
- Ensure the effective ended_at is not before the effective started_at    (rule 3)
  after a partial update (cross-field ordering guard for sparse PATCH).
- Verify an irrigation event exists before applying an update.            (rule 4)
- Verify an irrigation event exists before deletion.                      (rule 5)

Validation delegation
---------------------
The following invariants are enforced by the Pydantic schema layer and are
NOT re-validated here:

- Timezone-awareness of ``started_at``  — ``@field_validator`` on
  IrrigationEventCreate and IrrigationEventUpdate.
- Timezone-awareness of ``ended_at``    — ``@field_validator`` on both schemas.
- ``ended_at >= started_at`` when both are present in the same payload  —
  ``@model_validator`` on IrrigationEventCreate and IrrigationEventUpdate.
- ``duration_minutes >= 0``             — ``ge=0`` on both schemas.
- ``water_volume_liters >= 0``          — ``ge=0`` on both schemas.

The service layer adds the future-timestamp guard (rule 2) and the
cross-field ordering guard for sparse PATCH payloads (rule 3) that Pydantic
cannot enforce because it operates only on the inbound payload in isolation,
without access to the persisted record or current server time.

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.irrigation_event import IrrigationEvent
from app.db.repositories.field import FieldRepository
from app.db.repositories.irrigation_event import IrrigationEventRepository
from app.schemas.irrigation_event import IrrigationEventCreate, IrrigationEventUpdate
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class IrrigationEventNotFoundError(ValueError):
    """Raised when the referenced irrigation event does not exist."""


class InvalidIrrigationTimestampError(ValueError):
    """
    Raised when a timestamp invariant is violated at the service layer.

    Two invariants are enforced here that Pydantic cannot cover:

    1. ``started_at`` must not be in the future — irrigation is a past or
       present management action.  A future ``started_at`` would corrupt
       chronological irrigation history and produce misleading water-balance
       analytics.

    2. After a sparse PATCH, the effective ``ended_at`` must not precede the
       effective ``started_at``.  Pydantic's ``@model_validator`` on
       ``IrrigationEventUpdate`` only fires when both timestamps are present
       in the same payload; this guard covers the remaining cases where only
       one side is changed and the resulting pair would be inconsistent
       relative to the stored value of the other.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class IrrigationEventService:
    """
    Encapsulates all business logic for IrrigationEvent operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        irrigation_event_repository: IrrigationEventRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._events = irrigation_event_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_irrigation_event(
        self,
        field_id: uuid.UUID,
        payload: IrrigationEventCreate,
    ) -> IrrigationEvent:
        """
        Persist a new irrigation event for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        InvalidIrrigationTimestampError
            If ``started_at`` is in the future.
        """
        log = logger.bind(
            field_id=str(field_id),
            irrigation_method=payload.irrigation_method.value,
        )

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("irrigation_event_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 2 — started_at must not be in the future
        _validate_not_future(started_at=payload.started_at, log=log)

        data: dict[str, Any] = {
            "field_id": field_id,
            **payload.model_dump(),
        }
        event = await self._events.create(data)
        log.info(
            "irrigation_event_service.create.success",
            event_id=str(event.id),
        )

        # ── Future extension point ─────────────────────────────────────────────
        # This is the intended boundary for the following integrations.
        # Do NOT implement here; wire in a dedicated event-publishing adapter:
        #
        # - IrrigationEventCreated event → Redpanda / Kafka topic
        # - Digital Twin field water-balance state update
        # - CQRS read-model projection
        # - GaaS IrrigationAdvisor tool layer
        # - Temporal workflow initiation (e.g. irrigation compliance checks)
        # ──────────────────────────────────────────────────────────────────────

        return event

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_irrigation_event(
        self,
        event_id: uuid.UUID,
    ) -> IrrigationEvent | None:
        """
        Return a single irrigation event by primary key.

        Returns ``None`` when no event with ``event_id`` exists so that callers
        can decide whether a missing resource is an error (e.g. raise HTTP 404).
        """
        event = await self._events.get_by_id(event_id)
        if event is None:
            logger.bind(event_id=str(event_id)).debug(
                "irrigation_event_service.get.not_found"
            )
        return event

    async def list_field_irrigation_events(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[IrrigationEvent]:
        """
        Return all irrigation events belonging to a field, ordered by
        started_at descending (most recent event first).

        An empty list is returned when the field has no events or does not
        exist; field validation at list-time is the responsibility of the
        caller when required.  Repository ordering (``ORDER BY started_at DESC``)
        is authoritative; no reordering is applied in this layer.
        """
        return await self._events.list_by_field(
            field_id,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_irrigation_event(
        self,
        event_id: uuid.UUID,
        payload: IrrigationEventUpdate,
    ) -> IrrigationEvent:
        """
        Apply a partial update to an existing irrigation event.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.

        The service applies one guard that Pydantic cannot: the cross-field
        timestamp ordering check (rule 3) for sparse PATCH payloads that supply
        only one of ``started_at`` or ``ended_at``.  Effective values (incoming
        payload merged with the stored record) are used to evaluate the
        invariant, mirroring the ``WeatherRecordService`` pattern for
        temperature-range validation.

        Raises
        ------
        IrrigationEventNotFoundError
            If no irrigation event with ``event_id`` exists.
        InvalidIrrigationTimestampError
            If the supplied ``started_at`` is in the future, or if the
            effective ``ended_at`` would precede the effective ``started_at``
            after the update is applied.
        """
        log = logger.bind(event_id=str(event_id))

        # Rule 4 — event must exist before update
        current = await self._events.get_by_id(event_id)
        if current is None:
            log.warning("irrigation_event_service.update.not_found")
            raise IrrigationEventNotFoundError(
                f"Irrigation event '{event_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 2 — validate future guard only if the caller is changing started_at
        if "started_at" in update_data:
            _validate_not_future(started_at=update_data["started_at"], log=log)

        # Rule 3 — cross-field ordering guard for sparse PATCH payloads.
        # Pydantic's @model_validator on IrrigationEventUpdate only fires when
        # both started_at and ended_at are present in the same payload.  The
        # service must cover the remaining cases:
        #   - only started_at changed → check stored ended_at >= new started_at
        #   - only ended_at changed   → check new ended_at >= stored started_at
        # Resolve effective values: incoming payload takes priority; fall back
        # to the stored value for any field not being changed.
        _validate_ended_at_ordering(
            started_at=update_data.get("started_at", current.started_at),
            ended_at=update_data.get("ended_at", current.ended_at),
            log=log,
        )

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._events.update(event_id, update_data)
        log.info("irrigation_event_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_irrigation_event(self, event_id: uuid.UUID) -> None:
        """
        Permanently remove an irrigation event.

        ``IrrigationEventRepository.delete`` returns ``False`` when the record
        is absent, which satisfies rule 5 without requiring a separate existence
        query.

        Raises
        ------
        IrrigationEventNotFoundError
            If no irrigation event with ``event_id`` exists.
        """
        log = logger.bind(event_id=str(event_id))

        # Rule 5 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._events.delete(event_id)
        if not deleted:
            log.warning("irrigation_event_service.delete.not_found")
            raise IrrigationEventNotFoundError(
                f"Irrigation event '{event_id}' does not exist."
            )

        log.info("irrigation_event_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_not_future(
    *,
    started_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidIrrigationTimestampError`` if ``started_at`` is in the future.

    The comparison is performed in UTC regardless of the incoming timezone so
    that events from fields in non-UTC offsets are evaluated correctly.
    Pydantic already guarantees timezone-awareness at this point, so the
    naive-datetime branch (``replace(tzinfo=timezone.utc)``) is retained as a
    defence-in-depth guard for programmatic callers that bypass the schema layer.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    now_utc = datetime.now(timezone.utc)
    started_at_utc = (
        started_at.replace(tzinfo=timezone.utc)
        if started_at.tzinfo is None
        else started_at.astimezone(timezone.utc)
    )
    if started_at_utc > now_utc:
        log.warning(
            "irrigation_event_service.timestamp_future",
            started_at=started_at.isoformat(),
        )
        raise InvalidIrrigationTimestampError(
            f"started_at ({started_at.isoformat()}) cannot be in the future."
        )


def _validate_ended_at_ordering(
    *,
    started_at: datetime,
    ended_at: datetime | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidIrrigationTimestampError`` if ``ended_at`` precedes
    ``started_at``.

    Called at update time with the effective values — the incoming payload merged
    with the stored record — so that sparse PATCH payloads that change only one
    timestamp are evaluated against the correct counterpart value.  When
    ``ended_at`` is ``None`` the check is skipped; an event without a recorded
    end time is valid.

    Pydantic's ``@model_validator`` on ``IrrigationEventUpdate`` already validates
    this constraint when both timestamps are present in the same payload.  This
    helper covers the complementary cases where only one side changes.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if ended_at is not None and ended_at < started_at:
        log.warning(
            "irrigation_event_service.ended_at_before_started_at",
            started_at=started_at.isoformat(),
            ended_at=ended_at.isoformat(),
        )
        raise InvalidIrrigationTimestampError(
            f"ended_at ({ended_at.isoformat()}) must be greater than or equal to "
            f"started_at ({started_at.isoformat()})."
        )
