"""
YieldRecordService — business logic for the YieldRecord domain.

Responsibilities
----------------
- Verify the parent crop exists before creating a yield record.          (rule 1)
- Resolve field_id from the crop record server-side.                     (rule 2)
- Ensure recorded_at is not in the future.                               (rule 3)
- Ensure area_harvested_ha is > 0 when supplied.                         (rule 4)
- Ensure test_weight_kg_hl is > 0 when supplied.                         (rule 5)
- Verify a yield record exists before applying an update.                (rule 6)
- Verify a yield record exists before deletion.                          (rule 7)

Validation delegation
---------------------
The following invariants are enforced by the Pydantic schema layer and are
NOT re-validated here:

- Timezone-awareness of ``recorded_at``         — ``@field_validator`` on
  YieldRecordCreate and YieldRecordUpdate.
- ``yield_value_tons_ha >= 0``                  — ``ge=0`` on both schemas.
- ``moisture_content_percent`` in [0, 100]      — ``ge=0, le=100`` on both schemas.
- ``area_harvested_ha >= 0``                    — ``ge=0`` on both schemas.
- ``test_weight_kg_hl >= 0``                    — ``ge=0`` on both schemas.
- ``quality_grade`` max 50 characters          — ``max_length=50`` on both schemas.

The service layer adds:
- The future-timestamp guard (rule 3) — requires UTC clock comparison that
  Pydantic cannot safely perform.
- ``area_harvested_ha > 0`` (not merely >= 0) guard (rules 4, 5) — zero area
  or zero test weight is agronomically invalid; Pydantic allows exactly zero
  but the service tightens this (ADR-009-06).

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``CropNotFoundError`` is imported from ``app.services.crop`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.  This mirrors the
``FieldNotFoundError`` reuse pattern in ``IrrigationEventService``.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.yield_record import YieldRecord
from app.db.repositories.crop import CropRepository
from app.db.repositories.yield_record import YieldRecordRepository
from app.schemas.yield_record import YieldRecordCreate, YieldRecordUpdate
from app.services.crop import CropNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class YieldRecordNotFoundError(ValueError):
    """Raised when the referenced yield record does not exist."""


class InvalidYieldRecordError(ValueError):
    """
    Raised when a yield measurement value violates agronomic business rules
    at the service layer.

    Two invariants are enforced here that Pydantic cannot cover:

    1. ``recorded_at`` must not be in the future — yield is a past or present
       observation.  A future ``recorded_at`` would corrupt chronological yield
       history and produce misleading feature vectors for the Yield Prediction
       Engine.

    2. ``area_harvested_ha``, when supplied, must be > 0.  Pydantic allows
       exactly zero (ge=0) but an observation with zero harvested area is
       agronomically meaningless (ADR-009-06).

    3. ``test_weight_kg_hl``, when supplied, must be > 0.  Same reasoning —
       zero test weight is a data entry error, not a valid measurement.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class YieldRecordService:
    """
    Encapsulates all business logic for YieldRecord operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        yield_record_repository: YieldRecordRepository,
        crop_repository: CropRepository,
    ) -> None:
        self._records = yield_record_repository
        self._crops = crop_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_yield_record(
        self,
        crop_id: uuid.UUID,
        payload: YieldRecordCreate,
    ) -> YieldRecord:
        """
        Persist a new yield record for the given crop cycle.

        ``field_id`` is resolved server-side from the crop record (ADR-009-02)
        rather than being supplied by the caller; this guarantees that the
        denormalized ``field_id`` column is always consistent with the crop's
        actual field.

        Raises
        ------
        CropNotFoundError
            If no crop with ``crop_id`` exists.
        InvalidYieldRecordError
            If ``recorded_at`` is in the future, ``area_harvested_ha`` is
            supplied and <= 0, or ``test_weight_kg_hl`` is supplied and <= 0.
        """
        log = logger.bind(
            crop_id=str(crop_id),
            measurement_method=payload.measurement_method.value,
        )

        # Rule 1 — parent crop must exist
        crop = await self._crops.get_by_id(crop_id)
        if crop is None:
            log.warning("yield_record_service.create.crop_not_found")
            raise CropNotFoundError(f"Crop '{crop_id}' does not exist.")

        # Rule 2 — resolve field_id from the crop record
        field_id: uuid.UUID = crop.field_id

        # Rule 3 — recorded_at must not be in the future
        _validate_not_future(recorded_at=payload.recorded_at, log=log)

        # Rules 4, 5 — agronomic measurement guards
        _validate_area(area_harvested_ha=payload.area_harvested_ha, log=log)
        _validate_test_weight(test_weight_kg_hl=payload.test_weight_kg_hl, log=log)

        data: dict[str, Any] = {
            "crop_id": crop_id,
            "field_id": field_id,
            **payload.model_dump(),
        }
        record = await self._records.create(data)
        log.info(
            "yield_record_service.create.success",
            record_id=str(record.id),
            field_id=str(field_id),
        )

        # ── Future extension point ─────────────────────────────────────────────
        # This is the intended boundary for the following integrations.
        # Do NOT implement here; wire in a dedicated event-publishing adapter:
        #
        # - YieldRecordCreated event → Redpanda / Kafka topic
        # - Digital Twin field productivity state update
        # - CQRS read-model projection
        # - Phase 12 Yield Prediction Engine feature pipeline trigger
        # - GaaS YieldAdvisor tool layer
        # ──────────────────────────────────────────────────────────────────────

        return record

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_yield_record(
        self,
        record_id: uuid.UUID,
    ) -> YieldRecord | None:
        """
        Return a single yield record by primary key.

        Returns ``None`` when no record with ``record_id`` exists so that
        callers can decide whether a missing resource is an error
        (e.g. raise HTTP 404).
        """
        record = await self._records.get_by_id(record_id)
        if record is None:
            logger.bind(record_id=str(record_id)).debug(
                "yield_record_service.get.not_found"
            )
        return record

    async def list_crop_yield_records(
        self,
        crop_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[YieldRecord]:
        """
        Return all yield records belonging to a crop cycle, ordered by
        recorded_at descending (most recent measurement first).

        An empty list is returned when the crop has no records or does not
        exist; crop validation at list-time is the responsibility of the
        caller when required.
        """
        return await self._records.list_by_crop(
            crop_id,
            limit=limit,
            offset=offset,
        )

    async def list_field_yield_records(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[YieldRecord]:
        """
        Return all yield records for a field across all crop cycles, ordered
        by recorded_at descending (most recent measurement first).

        Uses the denormalized ``field_id`` column for a direct field-scoped
        query without a JOIN through crops (ADR-009-02).
        """
        return await self._records.list_by_field(
            field_id,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_yield_record(
        self,
        record_id: uuid.UUID,
        payload: YieldRecordUpdate,
    ) -> YieldRecord:
        """
        Apply a partial update to an existing yield record.

        Only the fields present in ``payload`` are modified; absent fields
        keep their current values.

        ``crop_id`` and ``field_id`` are immutable after creation and are
        excluded from ``YieldRecordUpdate`` at the schema level (ADR-009-05).
        The repository's sparse-patch approach (``exclude_unset=True``) means
        neither field can be accidentally overwritten.

        Raises
        ------
        YieldRecordNotFoundError
            If no yield record with ``record_id`` exists.
        InvalidYieldRecordError
            If the supplied ``recorded_at`` is in the future, or if
            ``area_harvested_ha`` or ``test_weight_kg_hl`` are supplied
            and <= 0.
        """
        log = logger.bind(record_id=str(record_id))

        # Rule 6 — record must exist before update
        current = await self._records.get_by_id(record_id)
        if current is None:
            log.warning("yield_record_service.update.not_found")
            raise YieldRecordNotFoundError(
                f"Yield record '{record_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 3 — validate future guard only if the caller is changing recorded_at
        if "recorded_at" in update_data:
            _validate_not_future(recorded_at=update_data["recorded_at"], log=log)

        # Rules 4, 5 — validate agronomic guards only for fields being changed
        if "area_harvested_ha" in update_data:
            _validate_area(area_harvested_ha=update_data["area_harvested_ha"], log=log)

        if "test_weight_kg_hl" in update_data:
            _validate_test_weight(
                test_weight_kg_hl=update_data["test_weight_kg_hl"], log=log
            )

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._records.update(record_id, update_data)
        log.info("yield_record_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_yield_record(self, record_id: uuid.UUID) -> None:
        """
        Permanently remove a yield record.

        ``YieldRecordRepository.delete`` returns ``False`` when the record is
        absent, which satisfies rule 7 without requiring a separate existence
        query.

        Raises
        ------
        YieldRecordNotFoundError
            If no yield record with ``record_id`` exists.
        """
        log = logger.bind(record_id=str(record_id))

        # Rule 7 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._records.delete(record_id)
        if not deleted:
            log.warning("yield_record_service.delete.not_found")
            raise YieldRecordNotFoundError(
                f"Yield record '{record_id}' does not exist."
            )

        log.info("yield_record_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_not_future(
    *,
    recorded_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidYieldRecordError`` if ``recorded_at`` is in the future.

    The comparison is performed in UTC regardless of the incoming timezone so
    that measurements from fields in non-UTC offsets are evaluated correctly.
    Pydantic already guarantees timezone-awareness at this point, so the
    naive-datetime branch (``replace(tzinfo=timezone.utc)``) is retained as a
    defence-in-depth guard for programmatic callers that bypass the schema layer.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    now_utc = datetime.now(timezone.utc)
    recorded_at_utc = (
        recorded_at.replace(tzinfo=timezone.utc)
        if recorded_at.tzinfo is None
        else recorded_at.astimezone(timezone.utc)
    )
    if recorded_at_utc > now_utc:
        log.warning(
            "yield_record_service.timestamp_future",
            recorded_at=recorded_at.isoformat(),
        )
        raise InvalidYieldRecordError(
            f"recorded_at ({recorded_at.isoformat()}) cannot be in the future."
        )


def _validate_area(
    *,
    area_harvested_ha: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidYieldRecordError`` if ``area_harvested_ha`` is supplied
    and is not greater than zero.

    Pydantic's ``ge=0`` constraint allows exactly zero, but an observation
    with zero harvested area is agronomically meaningless — it cannot
    represent a real sub-field measurement (ADR-009-06).

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if area_harvested_ha is not None and area_harvested_ha <= 0:
        log.warning(
            "yield_record_service.invalid_area",
            area_harvested_ha=str(area_harvested_ha),
        )
        raise InvalidYieldRecordError(
            f"area_harvested_ha ({area_harvested_ha}) must be greater than zero "
            "when supplied."
        )


def _validate_test_weight(
    *,
    test_weight_kg_hl: Decimal | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidYieldRecordError`` if ``test_weight_kg_hl`` is supplied
    and is not greater than zero.

    Pydantic's ``ge=0`` constraint allows exactly zero, but a test weight of
    zero is a data entry error — grain with zero bulk density cannot exist.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if test_weight_kg_hl is not None and test_weight_kg_hl <= 0:
        log.warning(
            "yield_record_service.invalid_test_weight",
            test_weight_kg_hl=str(test_weight_kg_hl),
        )
        raise InvalidYieldRecordError(
            f"test_weight_kg_hl ({test_weight_kg_hl}) must be greater than zero "
            "when supplied."
        )
