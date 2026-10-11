"""
FeatureStoreService — materialises CDD feature vectors for fields.

Reads bounded windows from TimescaleDB continuous aggregates (ADR-004) and
persists immutable snapshots for ML engines and downstream read models.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.models.field import Field
from app.db.models.field_feature_snapshot import FieldFeatureSnapshot
from app.db.repositories.feature_extraction import FeatureExtractionRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.features.catalog import FEATURE_CATALOG, registry_version
from app.features.types import FeatureId
from app.services.field import FieldNotFoundError

logger = get_logger(__name__)


class FeatureSnapshotNotFoundError(ValueError):
    """Raised when a feature snapshot id does not exist for the field."""


class FeatureStoreService:
    def __init__(
        self,
        field_repository: FieldRepository,
        snapshot_repository: FieldFeatureSnapshotRepository,
        extraction_repository: FeatureExtractionRepository,
    ) -> None:
        self._fields = field_repository
        self._snapshots = snapshot_repository
        self._extraction = extraction_repository

    async def materialize_field_snapshot(
        self,
        field_id: uuid.UUID,
        *,
        crop_id: uuid.UUID | None = None,
        as_of: datetime | None = None,
    ) -> FieldFeatureSnapshot:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")

        reference = as_of or datetime.now(timezone.utc)
        if reference.tzinfo is None:
            reference = reference.replace(tzinfo=timezone.utc)

        settings = get_settings()
        gdd_base = settings.FEATURE_STORE_GDD_BASE_C
        reg_version = settings.FEATURE_STORE_REGISTRY_VERSION or registry_version()

        features, notes = await self._compute_features(field, crop_id, reference, gdd_base)

        snapshot = await self._snapshots.create(
            {
                "field_id": field_id,
                "crop_id": crop_id,
                "registry_version": reg_version,
                "as_of": reference,
                "features": features,
                "materialization_notes": notes,
            }
        )

        logger.info(
            "feature_store.materialize.success",
            field_id=str(field_id),
            snapshot_id=str(snapshot.id),
            registry_version=reg_version,
        )
        return snapshot

    async def get_latest_snapshot(
        self,
        field_id: uuid.UUID,
    ) -> FieldFeatureSnapshot | None:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")
        settings = get_settings()
        return await self._snapshots.get_latest_for_field(
            field_id,
            registry_version=settings.FEATURE_STORE_REGISTRY_VERSION or None,
        )

    async def get_snapshot(
        self,
        field_id: uuid.UUID,
        snapshot_id: uuid.UUID,
    ) -> FieldFeatureSnapshot:
        snapshot = await self._snapshots.get_by_id(snapshot_id)
        if snapshot is None or snapshot.field_id != field_id:
            raise FeatureSnapshotNotFoundError(
                f"Feature snapshot {snapshot_id} not found for field {field_id}."
            )
        return snapshot

    async def list_snapshots(
        self,
        field_id: uuid.UUID,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[FieldFeatureSnapshot]:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")
        return await self._snapshots.list_for_field(field_id, limit=limit, offset=offset)

    async def _compute_features(
        self,
        field: Field,
        crop_id: uuid.UUID | None,
        as_of: datetime,
        gdd_base: float,
    ) -> tuple[dict[str, Any], str | None]:
        field_id = field.id
        notes: list[str] = []
        payload: dict[str, Any] = {}

        for feature_id, entry in FEATURE_CATALOG.items():
            window_start = as_of - timedelta(days=entry.window_days)
            value: float | str | None = None
            source = entry.primary_source

            if feature_id == FeatureId.SM_7D_MEAN:
                value = await self._extraction.soil_moisture_7d_mean(field_id, window_start, as_of)
            elif feature_id == FeatureId.RAINFALL_14D_SUM:
                value = await self._extraction.rainfall_14d_sum(field_id, window_start, as_of)
            elif feature_id == FeatureId.GDD_30D_SUM:
                value = await self._extraction.gdd_30d_sum(
                    field_id, window_start, as_of, gdd_base=gdd_base
                )
            elif feature_id == FeatureId.NDVI_90D_MAX:
                value = await self._extraction.ndvi_90d_max(field_id, window_start, as_of)
            elif feature_id == FeatureId.IRRIGATION_30D_MM:
                liters = await self._extraction.irrigation_volume_liters_30d(
                    field_id, window_start, as_of
                )
                if liters is not None and liters > 0:
                    value = self._extraction.liters_to_mm(liters, field.area_hectares)
                    if value is None:
                        notes.append("irrigation_30d_mm skipped — field area_hectares not set")
                else:
                    value = 0.0 if liters == 0 else None
            elif feature_id == FeatureId.DISEASE_SEVERITY_MAX:
                value = await self._extraction.disease_severity_max(
                    field_id, window_start, as_of, crop_id
                )
            elif feature_id == FeatureId.YIELD_ACTUAL:
                value = await self._extraction.latest_yield_tons_ha(field_id, crop_id)

            payload[feature_id.value] = {
                "value": value,
                "unit": entry.unit,
                "source": source,
                "window_days": entry.window_days,
                "available": value is not None,
            }

        note_str = "; ".join(notes) if notes else None
        return payload, note_str
