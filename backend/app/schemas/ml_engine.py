"""Schemas for ML engine stub API (Phase 14)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MLEngineCatalogItemResponse(BaseModel):
    engine_id: str
    display_name: str
    description: str
    engine_version: str
    recommendation_type: str
    trigger_events: list[str]


class MLEngineCatalogResponse(BaseModel):
    engines: list[MLEngineCatalogItemResponse]
    count: int = Field(ge=0)


class MLEngineRunResponse(BaseModel):
    engine_id: str
    engine_version: str
    field_id: uuid.UUID
    recommendation_id: uuid.UUID
    recommendation_type: str
    title: str
    created_at: datetime
