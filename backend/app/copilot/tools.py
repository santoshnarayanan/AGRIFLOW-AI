"""Farm Copilot tool registry — shared with MCP evaluation (Phase 16)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SensorType
from app.db.repositories.alert import AlertRepository
from app.db.repositories.field import FieldRepository
from app.db.repositories.field_digital_twin_state import FieldDigitalTwinStateRepository
from app.db.repositories.sensor_reading import SensorReadingRepository
from app.services.digital_twin import DigitalTwinService, DigitalTwinStateNotFoundError
from app.services.field import FieldNotFoundError
from app.services.read_model_projection import ReadModelProjectionService
from app.db.repositories.crop import CropRepository
from app.db.repositories.field_dashboard_read_model import FieldDashboardReadModelRepository
from app.db.repositories.field_feature_snapshot import FieldFeatureSnapshotRepository
from app.db.repositories.read_model_metrics import ReadModelMetricsRepository
from app.db.repositories.farm import FarmRepository


ToolHandler = Callable[[AsyncSession, dict[str, Any]], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class CopilotTool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: ToolHandler


async def _tool_get_field_context(session: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
    field_id = uuid.UUID(args["field_id"])
    field_repo = FieldRepository(session)
    field = await field_repo.get_by_id(field_id)
    if field is None:
        raise FieldNotFoundError(f"Field {field_id} does not exist.")
    farm_repo = FarmRepository(session)
    farm = await farm_repo.get_by_id(field.farm_id)
    return {
        "field_id": str(field.id),
        "field_name": field.name,
        "farm_id": str(field.farm_id),
        "farm_name": farm.name if farm else None,
        "area_hectares": float(field.area_hectares) if field.area_hectares else None,
    }


async def _tool_get_latest_soil_moisture(
    session: AsyncSession, args: dict[str, Any]
) -> dict[str, Any]:
    field_id = uuid.UUID(args["field_id"])
    repo = SensorReadingRepository(session)
    readings = await repo.latest_per_sensor_type(field_id)
    moisture = next((r for r in readings if r.sensor_type == SensorType.SOIL_MOISTURE), None)
    if moisture is None:
        return {"field_id": str(field_id), "soil_moisture": None}
    return {
        "field_id": str(field_id),
        "soil_moisture": float(moisture.sensor_value),
        "unit": moisture.unit,
        "recorded_at": moisture.recorded_at.isoformat(),
    }


async def _tool_get_open_alerts(session: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
    field_id = uuid.UUID(args["field_id"])
    repo = AlertRepository(session)
    alerts = await repo.list_by_field(field_id, limit=20)
    open_alerts = [
        {
            "id": str(a.id),
            "alert_type": a.alert_type.value,
            "severity": a.severity.value,
            "title": a.title,
            "is_acknowledged": a.is_acknowledged,
        }
        for a in alerts
        if not a.is_acknowledged
    ]
    return {"field_id": str(field_id), "open_alerts": open_alerts}


async def _tool_get_digital_twin_state(
    session: AsyncSession, args: dict[str, Any]
) -> dict[str, Any]:
    field_id = uuid.UUID(args["field_id"])
    projection = ReadModelProjectionService(
        farm_repository=FarmRepository(session),
        field_repository=FieldRepository(session),
        read_model_repository=FieldDashboardReadModelRepository(session),
        metrics_repository=ReadModelMetricsRepository(session),
        feature_snapshot_repository=FieldFeatureSnapshotRepository(session),
    )
    twin_service = DigitalTwinService(
        field_repository=FieldRepository(session),
        crop_repository=CropRepository(session),
        sensor_reading_repository=SensorReadingRepository(session),
        twin_state_repository=FieldDigitalTwinStateRepository(session),
        read_model_projection_service=projection,
    )
    try:
        state = await twin_service.get_field_state(field_id)
    except DigitalTwinStateNotFoundError:
        return {"field_id": str(field_id), "state_document": None}
    return {
        "field_id": str(field_id),
        "synchronized_at": state.synchronized_at.isoformat(),
        "state_document": state.state_document,
    }


async def _tool_get_dashboard_kpis(session: AsyncSession, args: dict[str, Any]) -> dict[str, Any]:
    field_id = uuid.UUID(args["field_id"])
    projection = ReadModelProjectionService(
        farm_repository=FarmRepository(session),
        field_repository=FieldRepository(session),
        read_model_repository=FieldDashboardReadModelRepository(session),
        metrics_repository=ReadModelMetricsRepository(session),
        feature_snapshot_repository=FieldFeatureSnapshotRepository(session),
    )
    dashboard = await projection.get_field_dashboard(field_id)
    return {
        "field_id": str(field_id),
        "projection_version": dashboard.projection_version,
        "kpi_payload": dashboard.kpi_payload,
        "refreshed_at": dashboard.refreshed_at.isoformat(),
        "open_alerts_count": dashboard.open_alerts_count,
        "active_recommendations_count": dashboard.active_recommendations_count,
    }


def build_copilot_tools() -> list[CopilotTool]:
    field_id_param = {
        "type": "object",
        "properties": {
            "field_id": {"type": "string", "format": "uuid", "description": "Target field UUID"},
        },
        "required": ["field_id"],
    }
    return [
        CopilotTool(
            name="get_field_context",
            description="Resolve farm and field metadata for agronomic reasoning.",
            parameters=field_id_param,
            handler=_tool_get_field_context,
        ),
        CopilotTool(
            name="get_latest_soil_moisture",
            description="Latest soil moisture telemetry for irrigation decisions.",
            parameters=field_id_param,
            handler=_tool_get_latest_soil_moisture,
        ),
        CopilotTool(
            name="get_open_alerts",
            description="List unacknowledged alerts for the field.",
            parameters=field_id_param,
            handler=_tool_get_open_alerts,
        ),
        CopilotTool(
            name="get_digital_twin_state",
            description="Current Digital Twin document for the field.",
            parameters=field_id_param,
            handler=_tool_get_digital_twin_state,
        ),
        CopilotTool(
            name="get_dashboard_kpis",
            description="CQRS dashboard KPIs and metrics for the field.",
            parameters=field_id_param,
            handler=_tool_get_dashboard_kpis,
        ),
    ]


def tools_by_name() -> dict[str, CopilotTool]:
    return {tool.name: tool for tool in build_copilot_tools()}


async def invoke_tool(
    session: AsyncSession,
    tool_name: str,
    arguments: dict[str, Any],
) -> dict[str, Any]:
    registry = tools_by_name()
    if tool_name not in registry:
        raise ValueError(f"Unknown tool: {tool_name}")
    return await registry[tool_name].handler(session, arguments)


def mcp_tool_catalog() -> list[dict[str, Any]]:
    """JSON-schema catalog for MCP-style tool discovery."""
    return [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.parameters,
        }
        for tool in build_copilot_tools()
    ]
