"""
DiseaseObservationService — business logic for the DiseaseObservation domain.

Responsibilities
----------------
- Verify the parent crop exists before creating a disease observation.     (rule 1)
- Resolve field_id from the crop record server-side.                       (rule 2)
- Ensure observed_at is not in the future.                                 (rule 3)
- Verify a disease observation exists before applying an update.           (rule 4)
- Verify a disease observation exists before deletion.                     (rule 5)

Validation delegation
---------------------
The following invariants are enforced by the Pydantic schema layer and are
NOT re-validated here:

- Timezone-awareness of ``observed_at``         — ``@field_validator`` on
  CreateDiseaseObservationRequest and UpdateDiseaseObservationRequest.
- ``affected_area_percent`` in [0, 100]         — ``ge=0, le=100`` on both schemas.
- ``disease_name`` max 255 characters           — ``max_length=255`` on both schemas.

The service layer adds:
- The future-timestamp guard (rule 3) — requires UTC clock comparison that
  Pydantic cannot safely perform.

All database access is delegated to the injected repositories; no SQLAlchemy
sessions or queries appear in this module.

``CropNotFoundError`` is imported from ``app.services.crop`` rather than
re-declared here; it is a shared domain exception, and importing it avoids a
naming collision in the services package ``__init__``.  This mirrors the
``FieldNotFoundError`` reuse pattern in ``IrrigationEventService``.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging.logger import get_logger
from app.db.models.disease_observation import DiseaseObservation
from app.db.repositories.crop import CropRepository
from app.db.repositories.disease_observation import DiseaseObservationRepository
from app.schemas.disease_observation import (
    CreateDiseaseObservationRequest,
    UpdateDiseaseObservationRequest,
)
from app.services.crop import CropNotFoundError  # shared domain exception

logger = get_logger(__name__)


# ── Domain exceptions ──────────────────────────────────────────────────────────


class DiseaseObservationNotFoundError(ValueError):
    """Raised when the referenced disease observation does not exist."""


class InvalidDiseaseObservationError(ValueError):
    """
    Raised when a disease observation value violates agronomic business rules
    at the service layer.

    One invariant is enforced here that Pydantic cannot cover:

    ``observed_at`` must not be in the future — disease pressure is a past or
    present observation.  A future ``observed_at`` would corrupt chronological
    disease history and produce misleading feature vectors for the Phase 13
    Disease Risk Scoring Engine.
    """


# ── Service ────────────────────────────────────────────────────────────────────


class DiseaseObservationService:
    """
    Encapsulates all business logic for DiseaseObservation operations.

    Constructor accepts repositories rather than a raw AsyncSession so that
    callers (e.g. FastAPI route dependencies) can compose and substitute
    implementations without touching service internals.
    """

    def __init__(
        self,
        disease_observation_repository: DiseaseObservationRepository,
        crop_repository: CropRepository,
    ) -> None:
        self._observations = disease_observation_repository
        self._crops = crop_repository

    # ── Create ─────────────────────────────────────────────────────────────────

    async def create_observation(
        self,
        crop_id: uuid.UUID,
        payload: CreateDiseaseObservationRequest,
    ) -> DiseaseObservation:
        """
        Persist a new disease observation for the given crop cycle.

        ``field_id`` is resolved server-side from the crop record (ADR-009-02)
        rather than being supplied by the caller; this guarantees that the
        denormalized ``field_id`` column is always consistent with the crop's
        actual field.

        Raises
        ------
        CropNotFoundError
            If no crop with ``crop_id`` exists.
        InvalidDiseaseObservationError
            If ``observed_at`` is in the future.
        """
        log = logger.bind(
            crop_id=str(crop_id),
            diagnosis_method=payload.diagnosis_method.value,
            severity=payload.severity.value,
        )

        # Rule 1 — parent crop must exist
        crop = await self._crops.get_by_id(crop_id)
        if crop is None:
            log.warning("disease_observation_service.create.crop_not_found")
            raise CropNotFoundError(f"Crop '{crop_id}' does not exist.")

        # Rule 2 — resolve field_id from the crop record
        field_id: uuid.UUID = crop.field_id

        # Rule 3 — observed_at must not be in the future
        _validate_observed_at(observed_at=payload.observed_at, log=log)

        data: dict[str, Any] = {
            "crop_id": crop_id,
            "field_id": field_id,
            **payload.model_dump(),
        }
        observation = await self._observations.create(data)
        log.info(
            "disease_observation_service.create.success",
            observation_id=str(observation.id),
            field_id=str(field_id),
        )

        # ── Future extension point ─────────────────────────────────────────────
        # This is the intended boundary for the following integrations.
        # Do NOT implement here; wire in a dedicated event-publishing adapter:
        #
        # - DiseaseObservationCreated event → Redpanda / Kafka topic
        # - Digital Twin crop health state update
        # - CQRS read-model projection
        # - Phase 13 Disease Risk Scoring Engine feature pipeline trigger
        # - GaaS PlantHealthAdvisor tool layer
        # ──────────────────────────────────────────────────────────────────────

        return observation

    # ── Read ───────────────────────────────────────────────────────────────────

    async def get_observation(
        self,
        observation_id: uuid.UUID,
    ) -> DiseaseObservation:
        """
        Return a single disease observation by primary key.

        Raises
        ------
        DiseaseObservationNotFoundError
            If no observation with ``observation_id`` exists.
        """
        log = logger.bind(observation_id=str(observation_id))
        observation = await self._observations.get_by_id(observation_id)
        if observation is None:
            log.warning("disease_observation_service.get.not_found")
            raise DiseaseObservationNotFoundError(
                f"Disease observation '{observation_id}' does not exist."
            )
        return observation

    async def list_by_crop(
        self,
        crop_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DiseaseObservation]:
        """
        Return all disease observations belonging to a crop cycle, ordered by
        observed_at descending (most recent observation first).

        An empty list is returned when the crop has no observations or does
        not exist; crop validation at list-time is the responsibility of the
        caller when required.
        """
        return await self._observations.get_by_crop(
            crop_id,
            limit=limit,
            offset=offset,
        )

    async def list_by_field(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DiseaseObservation]:
        """
        Return all disease observations for a field across all crop cycles,
        ordered by observed_at descending (most recent observation first).

        Uses the denormalized ``field_id`` column for a direct field-scoped
        query without a JOIN through crops (ADR-009-02).
        """
        return await self._observations.get_by_field(
            field_id,
            limit=limit,
            offset=offset,
        )

    # ── Update ─────────────────────────────────────────────────────────────────

    async def update_observation(
        self,
        observation_id: uuid.UUID,
        payload: UpdateDiseaseObservationRequest,
    ) -> DiseaseObservation:
        """
        Apply a partial update to an existing disease observation.

        Only the fields present in ``payload`` are modified; absent fields
        keep their current values.

        ``crop_id`` and ``field_id`` are immutable after creation and are
        excluded from ``UpdateDiseaseObservationRequest`` at the schema level
        (ADR-009-05).  The repository's sparse-patch approach
        (``exclude_unset=True``) means neither field can be accidentally
        overwritten.

        Raises
        ------
        DiseaseObservationNotFoundError
            If no disease observation with ``observation_id`` exists.
        InvalidDiseaseObservationError
            If the supplied ``observed_at`` is in the future.
        """
        log = logger.bind(observation_id=str(observation_id))

        # Rule 4 — observation must exist before update
        current = await self._observations.get_by_id(observation_id)
        if current is None:
            log.warning("disease_observation_service.update.not_found")
            raise DiseaseObservationNotFoundError(
                f"Disease observation '{observation_id}' does not exist."
            )

        update_data = payload.model_dump(exclude_unset=True)

        # Rule 3 — validate future guard only if the caller is changing observed_at
        if "observed_at" in update_data:
            _validate_observed_at(observed_at=update_data["observed_at"], log=log)

        # update() returns None only when the record is absent; the guard above
        # guarantees existence, so the cast is safe.
        updated = await self._observations.update(observation_id, update_data)
        log.info("disease_observation_service.update.success")
        return updated  # type: ignore[return-value]

    # ── Delete ─────────────────────────────────────────────────────────────────

    async def delete_observation(self, observation_id: uuid.UUID) -> None:
        """
        Permanently remove a disease observation.

        ``DiseaseObservationRepository.delete`` returns ``False`` when the
        observation is absent, which satisfies rule 5 without requiring a
        separate existence query.

        Raises
        ------
        DiseaseObservationNotFoundError
            If no disease observation with ``observation_id`` exists.
        """
        log = logger.bind(observation_id=str(observation_id))

        # Rule 5 — BaseRepository.delete() performs get_by_id internally;
        # False means the observation was not found.
        deleted = await self._observations.delete(observation_id)
        if not deleted:
            log.warning("disease_observation_service.delete.not_found")
            raise DiseaseObservationNotFoundError(
                f"Disease observation '{observation_id}' does not exist."
            )

        log.info("disease_observation_service.delete.success")


# ── Internal helpers ───────────────────────────────────────────────────────────


def _validate_observed_at(
    *,
    observed_at: datetime,
    log: Any,
) -> None:
    """
    Raise ``InvalidDiseaseObservationError`` if ``observed_at`` is in the future.

    The comparison is performed in UTC regardless of the incoming timezone so
    that observations from fields in non-UTC offsets are evaluated correctly.
    Pydantic already guarantees timezone-awareness at this point, so the
    naive-datetime branch (``replace(tzinfo=timezone.utc)``) is retained as a
    defence-in-depth guard for programmatic callers that bypass the schema layer.

    Extracted as a module-level function so it can be unit-tested independently
    of the service class and database session lifecycle.
    """
    now_utc = datetime.now(timezone.utc)
    observed_at_utc = (
        observed_at.replace(tzinfo=timezone.utc)
        if observed_at.tzinfo is None
        else observed_at.astimezone(timezone.utc)
    )
    if observed_at_utc > now_utc:
        log.warning(
            "disease_observation_service.timestamp_future",
            observed_at=observed_at.isoformat(),
        )
        raise InvalidDiseaseObservationError(
            f"observed_at ({observed_at.isoformat()}) cannot be in the future."
        )
