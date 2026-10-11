"""
ReadModelProjectionService — builds and serves CQRS dashboard read models.

Slice 2 uses synchronous refresh from write-side tables; Phase 14 consumers
can call the same service asynchronously in a later slice.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.logging.logger import get_logger
from app.db.models.field import Field
from app.db.models.field_dashboard_read_model import FieldDashboardReadModel
from app.db.repositories.farm import FarmRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_dashboard_read_model import FieldDashboardReadModelRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.db.repositories.read_model_metrics import ReadModelMetricsRepository
from app.read_models.kpi import kpi_payload_from_snapshot
from app.services.farm import FarmNotFoundError
from app.services.field import FieldNotFoundError

logger = get_logger(__name__)

PROJECTION_VERSION = "v1"


class ReadModelProjectionService:
    def __init__(
        self,
        farm_repository: FarmRepository,
        field_repository: FieldRepository,
        read_model_repository: FieldDashboardReadModelRepository,
        metrics_repository: ReadModelMetricsRepository,
        feature_snapshot_repository: FieldFeatureSnapshotRepository,
    ) -> None:
        self._farms = farm_repository
        self._fields = field_repository
        self._read_models = read_model_repository
        self._metrics = metrics_repository
        self._feature_snapshots = feature_snapshot_repository

    async def refresh_field(self, field_id: uuid.UUID) -> FieldDashboardReadModel:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")
        return await self._project_field(field)

    async def refresh_farm(self, farm_id: uuid.UUID) -> list[FieldDashboardReadModel]:
        farm = await self._farms.get_by_id(farm_id)
        if farm is None:
            raise FarmNotFoundError(f"Farm {farm_id} does not exist.")
        fields = await self._fields.get_by_farm_id(farm_id, limit=5000)
        if not fields:
            return []
        projected: list[FieldDashboardReadModel] = []
        for field in fields:
            projected.append(await self._project_field(field))
        logger.info(
            "read_model.refresh_farm.success",
            farm_id=str(farm_id),
            field_count=len(projected),
        )
        return projected

    async def refresh_platform(self) -> int:
        fields = await self._fields.list_all(limit=5000)
        for field in fields:
            await self._project_field(field)
        logger.info("read_model.refresh_platform.success", field_count=len(fields))
        return len(fields)

    async def get_field_dashboard(self, field_id: uuid.UUID) -> FieldDashboardReadModel:
        field = await self._fields.get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field {field_id} does not exist.")
        model = await self._read_models.get_by_field_id(field_id)
        if model is None and get_settings().READ_MODEL_AUTO_REFRESH_ON_READ:
            return await self._project_field(field)
        if model is None:
            raise ReadModelNotMaterializedError(
                f"No dashboard read model for field {field_id}. Call refresh first."
            )
        return model

    async def get_farm_dashboard(self, farm_id: uuid.UUID) -> list[FieldDashboardReadModel]:
        farm = await self._farms.get_by_id(farm_id)
        if farm is None:
            raise FarmNotFoundError(f"Farm {farm_id} does not exist.")
        fields = await self._fields.get_by_farm_id(farm_id, limit=5000)
        if not fields:
            return []
        models = await self._read_models.list_by_farm_id(farm_id)
        if not models and get_settings().READ_MODEL_AUTO_REFRESH_ON_READ:
            return await self.refresh_farm(farm_id)
        return models

    async def get_platform_dashboard(self) -> dict[str, Any]:
        settings = get_settings()
        row_count = await self._read_models.count_rows()
        if row_count == 0 and settings.READ_MODEL_AUTO_REFRESH_ON_READ:
            await self.refresh_platform()
            row_count = await self._read_models.count_rows()

        open_alerts, critical_alerts, active_recs, materialized_fields = (
            await self._metrics.sum_field_projection_totals()
        )
        severity = await self._metrics.open_alert_severity_totals()
        total_farms = await self._metrics.count_farms()
        total_fields = await self._metrics.count_fields()
        refreshed_at = await self._read_models.latest_refreshed_at()
        with_features = await self._read_models.count_with_feature_snapshot()

        top_fields = await self._read_models.list_all(limit=5)
        top_fields.sort(key=lambda m: (m.critical_alerts_count, m.open_alerts_count), reverse=True)

        return {
            "is_materialized": row_count > 0,
            "projection_version": settings.READ_MODEL_PROJECTION_VERSION,
            "refreshed_at": refreshed_at,
            "total_farms": total_farms,
            "total_fields": total_fields,
            "materialized_fields": materialized_fields,
            "open_alerts": open_alerts,
            "critical_alerts": critical_alerts,
            "active_recommendations": active_recs,
            "fields_with_feature_snapshots": with_features,
            "alert_severity_breakdown": severity,
            "top_fields_by_pressure": [
                {
                    "field_id": str(m.field_id),
                    "farm_id": str(m.farm_id),
                    "field_name": m.field_name,
                    "open_alerts_count": m.open_alerts_count,
                    "critical_alerts_count": m.critical_alerts_count,
                    "active_recommendations_count": m.active_recommendations_count,
                }
                for m in top_fields
            ],
        }

    async def _project_field(self, field: Field) -> FieldDashboardReadModel:
        now = datetime.now(timezone.utc)
        open_alerts, critical = await self._metrics.alert_counts_for_field(field.id)
        active_recs = await self._metrics.active_recommendation_count_for_field(field.id)
        snapshot = await self._feature_snapshots.get_latest_for_field(field.id)

        data = {
            "farm_id": field.farm_id,
            "field_name": field.name,
            "open_alerts_count": open_alerts,
            "critical_alerts_count": critical,
            "active_recommendations_count": active_recs,
            "feature_snapshot_id": snapshot.id if snapshot else None,
            "feature_snapshot_as_of": snapshot.as_of if snapshot else None,
            "kpi_payload": kpi_payload_from_snapshot(snapshot),
            "projection_version": get_settings().READ_MODEL_PROJECTION_VERSION,
            "refreshed_at": now,
        }
        return await self._read_models.upsert_for_field(field.id, data)


class ReadModelNotMaterializedError(ValueError):
    """Raised when a read model has not been projected yet."""
