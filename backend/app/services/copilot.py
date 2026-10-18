"""Farm Copilot / GaaS orchestration (Phase 16)."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.logging.logger import get_logger
from app.core.observability.metrics import COPILOT_REQUESTS
from app.copilot.tools import invoke_tool, mcp_tool_catalog
from app.services.field import FieldNotFoundError
from app.db.repositories.field import FieldRepository

logger = get_logger(__name__)

_IRRIGATION_PATTERN = re.compile(r"\b(irrigat|water|moisture)\b", re.I)
_ALERT_PATTERN = re.compile(r"\balert", re.I)
_YIELD_PATTERN = re.compile(r"\byield|harvest\b", re.I)


class CopilotDisabledError(RuntimeError):
    """Raised when COPILOT_ENABLED is false."""


class FarmCopilotService:
    def __init__(self, session: AsyncSession, settings: Settings | None = None) -> None:
        self._session = session
        self._settings = settings or get_settings()

    async def chat(self, field_id: uuid.UUID, message: str) -> dict[str, Any]:
        if not self._settings.COPILOT_ENABLED:
            raise CopilotDisabledError("Farm Copilot is disabled.")

        field = await FieldRepository(self._session).get_by_id(field_id)
        if field is None:
            raise FieldNotFoundError(f"Field '{field_id}' does not exist.")

        tool_trace: list[dict[str, Any]] = []
        context = await invoke_tool(
            self._session,
            "get_field_context",
            {"field_id": str(field_id)},
        )
        tool_trace.append({"tool": "get_field_context", "result": context})

        if _IRRIGATION_PATTERN.search(message):
            moisture = await invoke_tool(
                self._session,
                "get_latest_soil_moisture",
                {"field_id": str(field_id)},
            )
            tool_trace.append({"tool": "get_latest_soil_moisture", "result": moisture})
        if _ALERT_PATTERN.search(message):
            alerts = await invoke_tool(
                self._session,
                "get_open_alerts",
                {"field_id": str(field_id)},
            )
            tool_trace.append({"tool": "get_open_alerts", "result": alerts})
        if _YIELD_PATTERN.search(message):
            kpis = await invoke_tool(
                self._session,
                "get_dashboard_kpis",
                {"field_id": str(field_id)},
            )
            tool_trace.append({"tool": "get_dashboard_kpis", "result": kpis})

        if self._settings.COPILOT_LLM_PROVIDER != "none":
            answer = await self._llm_answer(message, context, tool_trace)
            mode = self._settings.COPILOT_LLM_PROVIDER
        else:
            answer = self._deterministic_answer(message, context, tool_trace)
            mode = "deterministic"

        COPILOT_REQUESTS.labels(mode=mode).inc()
        return {
            "field_id": str(field_id),
            "mode": mode,
            "answer": answer,
            "tools": tool_trace,
            "mcp_catalog_size": len(mcp_tool_catalog()),
        }

    def _deterministic_answer(
        self,
        message: str,
        context: dict[str, Any],
        tool_trace: list[dict[str, Any]],
    ) -> str:
        field_name = context.get("field_name", "the field")
        lines = [
            f"Farm Copilot summary for **{field_name}** ({context.get('farm_name', 'farm')}).",
        ]
        for entry in tool_trace:
            result = entry["result"]
            if entry["tool"] == "get_latest_soil_moisture":
                val = result.get("soil_moisture")
                if val is None:
                    lines.append("No soil moisture sensor data is available yet.")
                else:
                    lines.append(
                        f"Latest soil moisture: {val}{result.get('unit', '%')} "
                        f"(recorded {result.get('recorded_at')})."
                    )
                    threshold = get_settings().SOIL_MOISTURE_LOW_THRESHOLD_PERCENT
                    if val < threshold:
                        lines.append(
                            f"Moisture is below the platform threshold ({threshold}%). "
                            "Consider irrigation and monitor alerts."
                        )
                    else:
                        lines.append("Moisture is within the configured threshold.")
            if entry["tool"] == "get_open_alerts":
                alerts = result.get("open_alerts", [])
                if not alerts:
                    lines.append("There are no open alerts for this field.")
                else:
                    titles = ", ".join(a["title"] for a in alerts[:5])
                    lines.append(f"Open alerts: {titles}.")
        if not any(t["tool"] != "get_field_context" for t in tool_trace):
            lines.append(
                "Ask about irrigation, alerts, or yield/harvest to pull live platform tools."
            )
        lines.append(f"(Query: {message.strip()[:200]})")
        return "\n".join(lines)

    async def _llm_answer(
        self,
        message: str,
        context: dict[str, Any],
        tool_trace: list[dict[str, Any]],
    ) -> str:
        settings = self._settings
        system = (
            "You are AGRIFLOW Farm Copilot. Answer using only the supplied tool JSON. "
            "Be concise and actionable for farm operators."
        )
        user_content = json.dumps(
            {"question": message, "field": context, "tool_results": tool_trace},
            default=str,
        )
        if settings.COPILOT_LLM_PROVIDER == "azure":
            if not settings.AZURE_OPENAI_ENDPOINT or not settings.AZURE_OPENAI_DEPLOYMENT:
                raise RuntimeError("Azure OpenAI is not configured.")
            url = (
                f"{settings.AZURE_OPENAI_ENDPOINT.rstrip('/')}/openai/deployments/"
                f"{settings.AZURE_OPENAI_DEPLOYMENT}/chat/completions"
                f"?api-version={settings.AZURE_OPENAI_API_VERSION}"
            )
            headers = {"api-key": settings.AZURE_OPENAI_API_KEY or ""}
            body = {
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.2,
            }
        else:
            if not settings.OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY is not configured.")
            url = f"{settings.OPENAI_API_BASE.rstrip('/')}/chat/completions"
            headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            body = {
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.2,
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("copilot.llm.unexpected_response", error=str(exc))
            raise RuntimeError("LLM response could not be parsed.") from exc
