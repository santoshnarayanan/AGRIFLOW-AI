"""
FieldService — business logic for the Field domain.

Responsibilities
----------------
- Verify the parent farm exists before creating a field.          (rule 1)
- Prevent duplicate field names (case-insensitive) within a farm. (rule 2)
- Verify a field exists before applying an update.                (rule 3)
- Verify a field exists before deletion.                          (rule 4)

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.
"""

import uuid
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.field import Field
from app.db.repositories.farm import FarmRepository
from app.db.repositories.field import FieldRepository
from app.schemas.field import FieldCreate, FieldUpdate

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class FarmNotFoundError(ValueError):
    """Raised when the referenced farm does not exist."""


class FieldNotFoundError(ValueError):
    """Raised when the referenced field does not exist."""


class DuplicateFieldNameError(ValueError):
    """Raised when a field with the same name already exists in the farm."""


# ── Service ────────────────────────────────────────────────────────────────────


class FieldService:
    """
    Encapsulates all business logic for Field operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        field_repository: FieldRepository,
        farm_repository: FarmRepository,
    ) -> None:
        self._fields = field_repository
        self._farms = farm_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_field(
        self,
        farm_id: uuid.UUID,
        payload: FieldCreate,
    ) -> Field:
        """
        Persist a new field under the given farm.

        Raises
        ------
        FarmNotFoundError
            If no farm with ``farm_id`` exists.
        DuplicateFieldNameError
            If a field with the same name (case-insensitive) already belongs to
            the farm.
        """
        log = logger.bind(farm_id=str(farm_id), field_name=payload.name)

        # Rule 1 — parent farm must exist
        farm = await self._farms.get_by_id(farm_id)
        if farm is None:
            log.warning("field_service.create.farm_not_found")
            raise FarmNotFoundError(f"Farm '{farm_id}' does not exist.")

        # Rule 2 — name must be unique within the farm (case-insensitive)
        existing_fields = await self._fields.get_by_farm_id(farm_id)
        if any(f.name.casefold() == payload.name.casefold() for f in existing_fields):
            log.warning("field_service.create.duplicate_name")
            raise DuplicateFieldNameError(
                f"A field named {payload.name!r} already exists in farm '{farm_id}'."
            )

        data: dict[str, Any] = {
            "farm_id": farm_id,
            **payload.model_dump(),
        }
        field = await self._fields.create(data)
        log.info("field_service.create.success", field_id=str(field.id))
        return field

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_field(self, field_id: uuid.UUID) -> Field | None:
        """
        Return a single field by primary key.

        Returns ``None`` when no field with ``field_id`` exists so that callers
        can decide whether a missing resource is an error.
        """
        field = await self._fields.get_by_id(field_id)
        if field is None:
            logger.bind(field_id=str(field_id)).debug("field_service.get.not_found")
        return field

    async def get_fields_by_farm(
        self,
        farm_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Field]:
        """
        Return all fields belonging to a farm, ordered by name.

        An empty list is returned when the farm has no fields or does not exist;
        farm validation is the responsibility of the caller when required.
        """
        return await self._fields.get_by_farm_id(farm_id, limit=limit, offset=offset)

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_field(
        self,
        field_id: uuid.UUID,
        payload: FieldUpdate,
    ) -> Field:
        """
        Apply a partial update to an existing field.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        DuplicateFieldNameError
            If the new name (when provided) is already taken by a sibling field
            in the same farm.
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 3 — field must exist before update
        current = await self._fields.get_by_id(field_id)
        if current is None:
            log.warning("field_service.update.not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        update_data = payload.model_dump(exclude_unset=True)

        # If the name is being changed, enforce uniqueness within the farm
        new_name: str | None = update_data.get("name")
        if new_name is not None and new_name.casefold() != current.name.casefold():
            siblings = await self._fields.get_by_farm_id(current.farm_id)
            if any(
                f.name.casefold() == new_name.casefold()
                for f in siblings
                if f.id != field_id
            ):
                log.warning("field_service.update.duplicate_name", new_name=new_name)
                raise DuplicateFieldNameError(
                    f"A field named {new_name!r} already exists in farm '{current.farm_id}'."
                )

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._fields.update(field_id, update_data)
        log.info("field_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_field(self, field_id: uuid.UUID) -> None:
        """
        Permanently remove a field.

        ``FieldRepository.delete`` returns ``False`` when the record is absent,
        which satisfies rule 4 without requiring a separate existence query.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 4 — FieldRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._fields.delete(field_id)
        if not deleted:
            log.warning("field_service.delete.not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        log.info("field_service.delete.success")
