"""
CropService — business logic for the Crop domain.

Responsibilities
----------------
- Verify the parent field exists before creating a crop.             (rule 1)
- Verify a crop exists before applying an update.                    (rule 2)
- Verify a crop exists before deletion.                              (rule 3)
- Ensure actual_harvest_date is not earlier than planting_date.      (rule 4)

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.
"""

import uuid
from datetime import date
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.crop import Crop, CropStatus
from app.db.repositories.crop import CropRepository
from app.db.repositories.field import FieldRepository
from app.schemas.crop import CropCreate, CropUpdate
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class CropNotFoundError(ValueError):
    """Raised when the referenced crop does not exist."""


class InvalidHarvestDateError(ValueError):
    """
    Raised when actual_harvest_date is set to a date earlier than planting_date.

    This is a business invariant — a crop cannot be harvested before it was
    planted — enforced here rather than in the database layer so that the
    error message is meaningful to API callers.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class CropService:
    """
    Encapsulates all business logic for Crop operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        crop_repository: CropRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._crops = crop_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_crop(
        self,
        field_id: uuid.UUID,
        payload: CropCreate,
    ) -> Crop:
        """
        Persist a new crop cycle under the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        """
        log = logger.bind(field_id=str(field_id), crop_name=payload.crop_name)

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("crop_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        data: dict[str, Any] = {
            "field_id": field_id,
            "status": CropStatus.PLANNED,
            **payload.model_dump(),
        }
        crop = await self._crops.create(data)
        log.info("crop_service.create.success", crop_id=str(crop.id))
        return crop

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_crop(self, crop_id: uuid.UUID) -> Crop | None:
        """
        Return a single crop by primary key.

        Returns ``None`` when no crop with ``crop_id`` exists so that callers
        can decide whether a missing resource is an error (e.g. raise HTTP 404).
        """
        crop = await self._crops.get_by_id(crop_id)
        if crop is None:
            logger.bind(crop_id=str(crop_id)).debug("crop_service.get.not_found")
        return crop

    async def list_field_crops(
        self,
        field_id: uuid.UUID,
        *,
        status: CropStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Crop]:
        """
        Return all crop cycles belonging to a field, ordered by planting_date
        descending (most recent cycle first).

        An empty list is returned when the field has no crops or does not exist;
        field validation at list-time is the responsibility of the caller when
        required.  The optional ``status`` filter is passed through to the
        repository as a pure DB predicate.
        """
        return await self._crops.list_by_field(
            field_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_crop(
        self,
        crop_id: uuid.UUID,
        payload: CropUpdate,
    ) -> Crop:
        """
        Apply a partial update to an existing crop cycle.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.

        Raises
        ------
        CropNotFoundError
            If no crop with ``crop_id`` exists.
        InvalidHarvestDateError
            If the effective actual_harvest_date (from payload or the stored
            value) would be earlier than the effective planting_date (from
            payload or the stored value).
        """
        log = logger.bind(crop_id=str(crop_id))

        # Rule 2 — crop must exist before update
        current = await self._crops.get_by_id(crop_id)
        if current is None:
            log.warning("crop_service.update.not_found")
            raise CropNotFoundError(f"Crop '{crop_id}' does not exist.")

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 4 — actual_harvest_date must not precede planting_date.
        # Evaluate against the *effective* values after the update is applied:
        # take the incoming value if the caller is changing it, otherwise fall
        # back to the value already stored on the record.
        _validate_harvest_date(
            planting_date=update_data.get("planting_date", current.planting_date),
            actual_harvest_date=update_data.get(
                "actual_harvest_date", current.actual_harvest_date
            ),
            log=log,
        )

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._crops.update(crop_id, update_data)
        log.info("crop_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_crop(self, crop_id: uuid.UUID) -> None:
        """
        Permanently remove a crop cycle.

        ``CropRepository.delete`` returns ``False`` when the record is absent,
        which satisfies rule 3 without requiring a separate existence query.

        Raises
        ------
        CropNotFoundError
            If no crop with ``crop_id`` exists.
        """
        log = logger.bind(crop_id=str(crop_id))

        # Rule 3 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._crops.delete(crop_id)
        if not deleted:
            log.warning("crop_service.delete.not_found")
            raise CropNotFoundError(f"Crop '{crop_id}' does not exist.")

        log.info("crop_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_harvest_date(
    *,
    planting_date: date,
    actual_harvest_date: date | None,
    log: Any,
) -> None:
    """
    Raise ``InvalidHarvestDateError`` if actual_harvest_date precedes
    planting_date.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    if actual_harvest_date is not None and actual_harvest_date < planting_date:
        log.warning(
            "crop_service.harvest_date_invalid",
            planting_date=str(planting_date),
            actual_harvest_date=str(actual_harvest_date),
        )
        raise InvalidHarvestDateError(
            f"actual_harvest_date ({actual_harvest_date}) cannot be earlier than "
            f"planting_date ({planting_date})."
        )
