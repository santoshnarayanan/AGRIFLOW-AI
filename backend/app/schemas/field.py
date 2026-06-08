"""
Pydantic schemas for the Field domain object.

Separation of concerns:
- FieldCreate   — inbound payload for POST (farm_id comes from the URL path, not body)
- FieldUpdate   — inbound payload for PATCH (all fields optional / partial update)
- FieldResponse — outbound representation returned to API consumers
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FieldCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the field",
    )
    area_hectares: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Field area in hectares",
    )
    soil_type: str | None = Field(
        default=None,
        max_length=50,
        description="Dominant soil classification for the field",
    )
    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
        decimal_places=6,
        description="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
        decimal_places=6,
        description="WGS-84 longitude — range [-180, 180]",
    )


class FieldUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Display name of the field",
    )
    area_hectares: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
        description="Field area in hectares",
    )
    soil_type: str | None = Field(
        default=None,
        max_length=50,
        description="Dominant soil classification for the field",
    )
    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
        decimal_places=6,
        description="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
        decimal_places=6,
        description="WGS-84 longitude — range [-180, 180]",
    )


class FieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key")
    farm_id: uuid.UUID = Field(description="UUID of the parent farm")
    name: str = Field(description="Display name of the field")
    area_hectares: Decimal | None = Field(description="Field area in hectares")
    soil_type: str | None = Field(description="Dominant soil classification for the field")
    latitude: Decimal | None = Field(description="WGS-84 latitude — range [-90, 90]")
    longitude: Decimal | None = Field(description="WGS-84 longitude — range [-180, 180]")
    created_at: datetime = Field(description="Row creation timestamp")
    updated_at: datetime = Field(description="Row last-updated timestamp")
