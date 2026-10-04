"""
Pydantic schemas for the Farm domain object.

Farm is the aggregate root of the AGRIFLOW-AI domain hierarchy:
    Farm → Field → Crop → ...

Separation of concerns
----------------------
- FarmCreate    — inbound payload for POST /farms
- FarmUpdate    — inbound payload for PATCH /farms/{farm_id}; all fields optional
- FarmResponse  — outbound representation returned to API consumers

Business rules enforced at schema layer:
- latitude must be in [-90, 90]
- longitude must be in [-180, 180]
- total_area_hectares must be > 0
- farm_code, farm_name, owner_name are non-empty strings
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmCreate(BaseModel):
    """Request body for POST /farms."""

    farm_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Short human-readable identifier, e.g. FARM-001 (must be unique)",
    )
    farm_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name of the farm",
    )
    owner_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Full name of the farm owner or managing entity",
    )
    country: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Country where the farm is located",
    )
    state: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="State or province",
    )
    city: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nearest city or municipality",
    )
    latitude: Decimal = Field(
        ...,
        ge=-90,
        le=90,
        description="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Decimal = Field(
        ...,
        ge=-180,
        le=180,
        description="WGS-84 longitude — range [-180, 180]",
    )
    total_area_hectares: Decimal = Field(
        ...,
        gt=0,
        description="Total farm area in hectares; must be greater than zero",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the farm is currently active; inactive farms are retained for history",
    )

    @field_validator("farm_code")
    @classmethod
    def strip_farm_code(cls, value: str) -> str:
        return value.strip()

    @field_validator("farm_name", "owner_name", "country", "state", "city")
    @classmethod
    def strip_string_fields(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank or whitespace-only.")
        return stripped


class FarmUpdate(BaseModel):
    """Request body for PATCH /farms/{farm_id}. All fields optional."""

    farm_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Display name of the farm",
    )
    owner_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Full name of the farm owner or managing entity",
    )
    country: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Country where the farm is located",
    )
    state: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="State or province",
    )
    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Nearest city or municipality",
    )
    latitude: Decimal | None = Field(
        default=None,
        ge=-90,
        le=90,
        description="WGS-84 latitude — range [-90, 90]",
    )
    longitude: Decimal | None = Field(
        default=None,
        ge=-180,
        le=180,
        description="WGS-84 longitude — range [-180, 180]",
    )
    total_area_hectares: Decimal | None = Field(
        default=None,
        gt=0,
        description="Total farm area in hectares; must be greater than zero",
    )
    is_active: bool | None = Field(
        default=None,
        description="Active status flag",
    )


class FarmResponse(BaseModel):
    """Outbound representation of a Farm returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the farm")
    farm_code: str = Field(description="Short human-readable identifier")
    farm_name: str = Field(description="Display name of the farm")
    owner_name: str = Field(description="Full name of the farm owner or managing entity")
    country: str = Field(description="Country where the farm is located")
    state: str = Field(description="State or province")
    city: str = Field(description="Nearest city or municipality")
    latitude: Decimal = Field(description="WGS-84 latitude")
    longitude: Decimal = Field(description="WGS-84 longitude")
    total_area_hectares: Decimal = Field(description="Total farm area in hectares")
    is_active: bool = Field(description="Whether the farm is currently active")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
