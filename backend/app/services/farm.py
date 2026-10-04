"""
FarmService — business logic for the Farm domain.

Responsibilities
----------------
- Validate farm_code uniqueness before creation.   (rule 1)
- Verify a farm exists before update.              (rule 2)
- Verify a farm exists before deletion.            (rule 3)
- Prevent deletion of farms that have child fields (cascade guard). (rule 4)

Farm is the aggregate root of the domain hierarchy. It is the first entity
created and the last to be deleted. The farm_code is a short human-readable
identifier that must be unique across the platform.
"""

import uuid
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.farm import Farm
from app.db.repositories.farm import FarmRepository
from app.schemas.farm import FarmCreate, FarmUpdate

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class FarmNotFoundError(ValueError):
    """Raised when the referenced farm does not exist."""


class DuplicateFarmCodeError(ValueError):
    """Raised when a farm_code already exists in the platform."""


class FarmHasFieldsError(ValueError):
    """Raised when attempting to delete a farm that still has child fields."""


# ── Service ────────────────────────────────────────────────────────────────────


class FarmService:
    """
    Encapsulates all business logic for Farm operations.

    Constructor accepts a repository rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(self, farm_repository: FarmRepository) -> None:
        self._farms = farm_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_farm(self, payload: FarmCreate) -> Farm:
        """
        Persist a new farm.

        Raises
        ------
        DuplicateFarmCodeError
            If a farm with the given farm_code already exists.
        """
        log = logger.bind(farm_code=payload.farm_code)

        # Rule 1 — farm_code must be unique
        existing = await self._farms.get_by_farm_code(payload.farm_code)
        if existing is not None:
            log.warning("farm_service.create.duplicate_code")
            raise DuplicateFarmCodeError(
                f"Farm with code '{payload.farm_code}' already exists."
            )

        data: dict[str, Any] = payload.model_dump()
        farm = await self._farms.create(data)
        log.info("farm_service.create.success", farm_id=str(farm.id))
        return farm

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_farm(self, farm_id: uuid.UUID) -> Farm | None:
        """Return a single farm by primary key, or None if not found."""
        farm = await self._farms.get_by_id(farm_id)
        if farm is None:
            logger.bind(farm_id=str(farm_id)).debug("farm_service.get.not_found")
        return farm

    async def list_farms(self, *, limit: int = 100, offset: int = 0) -> list[Farm]:
        """Return all farms ordered by creation date descending."""
        return await self._farms.get_all(limit=limit, offset=offset)

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_farm(self, farm_id: uuid.UUID, payload: FarmUpdate) -> Farm:
        """
        Apply a partial update to an existing farm.

        Raises
        ------
        FarmNotFoundError
            If no farm with ``farm_id`` exists.
        """
        log = logger.bind(farm_id=str(farm_id))

        # Rule 2 — farm must exist
        current = await self._farms.get_by_id(farm_id)
        if current is None:
            log.warning("farm_service.update.not_found")
            raise FarmNotFoundError(f"Farm '{farm_id}' does not exist.")

        update_data = payload.model_dump(exclude_unset=True)
        updated = await self._farms.update(farm_id, update_data)
        log.info("farm_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_farm(self, farm_id: uuid.UUID) -> None:
        """
        Permanently delete a farm and cascade to all child fields.

        The ORM cascade (delete-orphan) handles child deletion. The repository
        delete returns False when the record is absent.

        Raises
        ------
        FarmNotFoundError
            If no farm with ``farm_id`` exists.
        """
        log = logger.bind(farm_id=str(farm_id))

        deleted = await self._farms.delete(farm_id)
        if not deleted:
            log.warning("farm_service.delete.not_found")
            raise FarmNotFoundError(f"Farm '{farm_id}' does not exist.")

        log.info("farm_service.delete.success")
