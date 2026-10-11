"""Pydantic schemas for Digital Twin APIs."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.digital_twin.types import DIGITAL_TWIN_STATE_VERSION


class TwinStateSectionResponse(BaseModel):
    section: str
    description: str
    source: str


class DigitalTwinCatalogResponse(BaseModel):
    state_version: str = DIGITAL_TWIN_STATE_VERSION
    sections: list[TwinStateSectionResponse]
    count: int


class FieldDigitalTwinStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    field_id: uuid.UUID
    state_version: str
    state_document: dict[str, Any]
    synchronized_at: datetime
    created_at: datetime
    updated_at: datetime


class DigitalTwinSynchronizeResponse(BaseModel):
    field_id: uuid.UUID
    state_version: str
    synchronized_at: datetime
    state_id: uuid.UUID


class DigitalTwinPlatformSynchronizeResponse(BaseModel):
    synchronized_fields: int
    state_version: str = Field(default=DIGITAL_TWIN_STATE_VERSION)
