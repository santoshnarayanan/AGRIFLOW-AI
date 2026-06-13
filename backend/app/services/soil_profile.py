"""
SoilProfileService — business logic for the SoilProfile domain.

Responsibilities
----------------
- Verify the parent field exists before creating a soil profile.     (rule 1)
- Prevent duplicate soil profiles per field (one-to-one invariant).  (rule 2)
- Verify a soil profile exists before applying an update.            (rule 3)
- Verify a soil profile exists before deletion.                      (rule 4)
- Raise not-found when fetching a profile by field that has none.    (rule 5)

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``FieldNotFoundError`` is imported from ``app.services.field`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.
"""

import uuid
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.soil_profile import SoilProfile
from app.db.repositories.field import FieldRepository
from app.db.repositories.soil_profile import SoilProfileRepository
from app.schemas.soil_profile import SoilProfileCreate, SoilProfileUpdate
from app.services.field import FieldNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class SoilProfileNotFoundError(ValueError):
    """Raised when the referenced soil profile does not exist."""


class DuplicateSoilProfileError(ValueError):
    """
    Raised when a SoilProfile already exists for the given Field.

    The Field → SoilProfile relationship is one-to-one.  This invariant is
    enforced here at the service layer (using a lightweight repository probe)
    rather than relying solely on the UNIQUE database constraint, so that API
    callers receive a meaningful error message instead of a raw IntegrityError.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class SoilProfileService:
    """
    Encapsulates all business logic for SoilProfile operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        soil_profile_repository: SoilProfileRepository,
        field_repository: FieldRepository,
    ) -> None:
        self._profiles = soil_profile_repository
        self._fields = field_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_soil_profile(
        self,
        field_id: uuid.UUID,
        payload: SoilProfileCreate,
    ) -> SoilProfile:
        """
        Persist a new soil profile for the given field.

        Raises
        ------
        FieldNotFoundError
            If no field with ``field_id`` exists.
        DuplicateSoilProfileError
            If a soil profile already exists for the field.
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 1 — parent field must exist
        field = await self._fields.get_by_id(field_id)
        if field is None:
            log.warning("soil_profile_service.create.field_not_found")
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        # Rule 2 — only one profile per field (one-to-one invariant)
        if await self._profiles.exists_for_field(field_id):
            log.warning("soil_profile_service.create.duplicate_profile")
            raise DuplicateSoilProfileError(
                f"A soil profile already exists for field '{field_id}'."
            )

        data: dict[str, Any] = {
            "field_id": field_id,
            **payload.model_dump(),
        }
        profile = await self._profiles.create(data)
        log.info("soil_profile_service.create.success", profile_id=str(profile.id))
        return profile

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_soil_profile(self, profile_id: uuid.UUID) -> SoilProfile | None:
        """
        Return a single soil profile by primary key.

        Returns ``None`` when no profile with ``profile_id`` exists so that
        callers can decide whether a missing resource is an error (e.g. raise
        HTTP 404).
        """
        profile = await self._profiles.get_by_id(profile_id)
        if profile is None:
            logger.bind(profile_id=str(profile_id)).debug(
                "soil_profile_service.get.not_found"
            )
        return profile

    async def get_soil_profile_by_field(self, field_id: uuid.UUID) -> SoilProfile:
        """
        Return the soil profile for the given field.

        Unlike ``get_soil_profile``, this method raises rather than returns
        ``None`` because a missing profile for a known field is always an
        actionable error in the contexts where field-scoped lookup is used
        (e.g. GET /fields/{field_id}/soil-profile).

        Raises
        ------
        SoilProfileNotFoundError
            If the field has no associated soil profile.
        """
        log = logger.bind(field_id=str(field_id))

        # Rule 5 — raise if profile does not exist for the field
        profile = await self._profiles.get_by_field_id(field_id)
        if profile is None:
            log.warning("soil_profile_service.get_by_field.not_found")
            raise SoilProfileNotFoundError(
                f"No soil profile exists for field '{field_id}'."
            )

        return profile

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_soil_profile(
        self,
        profile_id: uuid.UUID,
        payload: SoilProfileUpdate,
    ) -> SoilProfile:
        """
        Apply a partial update to an existing soil profile.

        Only the fields present in ``payload`` are modified; absent fields keep
        their current values.

        Raises
        ------
        SoilProfileNotFoundError
            If no soil profile with ``profile_id`` exists.
        """
        log = logger.bind(profile_id=str(profile_id))

        # Rule 3 — profile must exist before update
        current = await self._profiles.get_by_id(profile_id)
        if current is None:
            log.warning("soil_profile_service.update.not_found")
            raise SoilProfileNotFoundError(
                f"Soil profile '{profile_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._profiles.update(profile_id, update_data)
        log.info("soil_profile_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_soil_profile(self, profile_id: uuid.UUID) -> None:
        """
        Permanently remove a soil profile.

        ``SoilProfileRepository.delete`` returns ``False`` when the record is
        absent, which satisfies rule 4 without requiring a separate existence
        query.

        Raises
        ------
        SoilProfileNotFoundError
            If no soil profile with ``profile_id`` exists.
        """
        log = logger.bind(profile_id=str(profile_id))

        # Rule 4 — BaseRepository.delete() performs get_by_id internally;
        # False means the record was not found.
        deleted = await self._profiles.delete(profile_id)
        if not deleted:
            log.warning("soil_profile_service.delete.not_found")
            raise SoilProfileNotFoundError(
                f"Soil profile '{profile_id}' does not exist."
            )

        log.info("soil_profile_service.delete.success")
