"""DigitalTwinService — synchronizes field state documents (Phase 15 slice 3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.models.field_digital_twin_state import FieldDigitalTwinState
from app.db.repositories.crop import CropRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_digital_twin_state import FieldDigitalTwinStateRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.digital_twin.document import build_field_digital_twin_document
from app.services.field import FieldNotFoundError
from app.services.read_model_projection import ReadModelProjectionService

logger = get_logger(__name__)


class DigitalTwinStateNotFoundError(ValueError):
    """Raised when twin state has not been synchronized yet."""


class DigitalTwinService:
    def __init__(
        self,
        field_repository: FieldRepository,
        crop_repository: CropRepository,
        sensor_reading_repository: SensorReadingRepository,
        twin_state_repository: FieldDigitalTwinStateRepository,
        read_model_projection_service: ReadModelProjectionService,
    ) -> None:
        self._fields = field_repository
        self._crops = crop_repository
        self._sensors = sensor_reading_repository
        self._twin_states = twin_state_repository
        self._read_models = read_model_projection_service

    async def synchronize_field(self, field_id: uuid.UUID) -> FieldDigitalTwinState:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")

        dashboard = await self._read_models.refresh_field(field_id)
        crops = await self._crops.list_by_field(field_id, limit=50)
        latest_sensors = await self._sensors.latest_per_sensor_type(field_id)
        now = datetime.now(timezone.utc)

        document = build_field_digital_twin_document(
            field,
            crops,
            latest_sensors,
            dashboard,
            synchronized_at=now,
        )
        settings = get_settings()
        state = await self._twin_states.upsert_for_field(
            field_id,
            {
                "state_version": settings.DIGITAL_TWIN_STATE_VERSION,
                "state_document": document,
                "synchronized_at": now,
            },
        )
        logger.info(
            "digital_twin.synchronize.success",
            field_id=str(field_id),
            state_id=str(state.id),
        )
        return state

    async def synchronize_platform(self) -> int:
        fields = await self._fields.list_all(limit=5000)
        for field in fields:
            await self.synchronize_field(field.id)
        return len(fields)

    async def get_field_state(self, field_id: uuid.UUID) -> FieldDigitalTwinState:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")

        state = await self._twin_states.get_by_field_id(field_id)
        if state is None and get_settings().DIGITAL_TWIN_AUTO_SYNC_ON_READ:
            return await self.synchronize_field(field_id)
        if state is None:
            raise DigitalTwinStateNotFoundError(
                f"No Digital Twin state for field {field_id}. Call synchronize first."
            )
        return state
