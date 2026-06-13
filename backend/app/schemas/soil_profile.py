"""
Pydantic schemas for the SoilProfile domain object.

Separation of concerns
----------------------
- SoilProfileBase   — shared field inventory; parent of SoilProfileResponse.
                      Defines the full set of agronomic measurement fields with
                      their validation rules so the rules are expressed once.
- SoilProfileCreate — inbound payload for POST /fields/{field_id}/soil-profile.
                      ``field_id`` is intentionally excluded; it is resolved from
                      the URL path by the router, matching the pattern used by
                      CropCreate.  ``soil_type`` is the only required field —
                      nutrient measurements may not yet be available at creation.
- SoilProfileUpdate — inbound payload for PATCH /fields/{field_id}/soil-profile.
                      Every field is optional to support sparse partial updates.
- SoilProfileResponse — outbound representation returned to API consumers.
                      Extends SoilProfileBase with server-assigned identity and
                      audit fields.  ``from_attributes=True`` enables direct
                      construction from a SQLAlchemy ORM instance.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.soil_profile import SoilType


class SoilProfileBase(BaseModel):
    """
    Shared field inventory for the SoilProfile domain.

    Inherited by SoilProfileResponse.  SoilProfileUpdate mirrors these fields
    but marks all of them optional, so it is defined separately rather than
    as a subclass.
    """

    soil_type: SoilType = Field(
        ...,
        description=(
            "Dominant soil texture classification "
            "(SANDY | CLAY | LOAM | SILT | PEAT | CHALK)"
        ),
    )
    ph: Decimal | None = Field(
        default=None,
        ge=0,
        le=14,
        decimal_places=2,
        description="Soil pH on the 0–14 scale; 7.00 is neutral",
    )
    organic_matter: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Organic matter content as a percentage by weight (e.g. 3.500 = 3.5%)",
    )
    nitrogen: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Total nitrogen concentration in mg/kg (ppm)",
    )
    phosphorus: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available phosphorus concentration in mg/kg (ppm)",
    )
    potassium: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available potassium concentration in mg/kg (ppm)",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text agronomist observations or lab report references",
    )


class SoilProfileCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/soil-profile.

    ``field_id`` is excluded — it is injected from the URL path by the router.
    ``soil_type`` is required; all nutrient measurements are optional because
    a profile may be created before full laboratory results are available.
    """

    soil_type: SoilType = Field(
        ...,
        description=(
            "Dominant soil texture classification "
            "(SANDY | CLAY | LOAM | SILT | PEAT | CHALK)"
        ),
    )
    ph: Decimal | None = Field(
        default=None,
        ge=0,
        le=14,
        decimal_places=2,
        description="Soil pH on the 0–14 scale; 7.00 is neutral",
    )
    organic_matter: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Organic matter content as a percentage by weight",
    )
    nitrogen: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Total nitrogen concentration in mg/kg (ppm)",
    )
    phosphorus: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available phosphorus concentration in mg/kg (ppm)",
    )
    potassium: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available potassium concentration in mg/kg (ppm)",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text agronomist observations or lab report references",
    )


class SoilProfileUpdate(BaseModel):
    """
    Request body for PATCH /fields/{field_id}/soil-profile.

    All fields are optional to support sparse partial updates.  The service
    layer applies only the fields explicitly provided by the caller.
    """

    soil_type: SoilType | None = Field(
        default=None,
        description="Dominant soil texture classification",
    )
    ph: Decimal | None = Field(
        default=None,
        ge=0,
        le=14,
        decimal_places=2,
        description="Soil pH on the 0–14 scale",
    )
    organic_matter: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Organic matter content as a percentage by weight",
    )
    nitrogen: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Total nitrogen concentration in mg/kg (ppm)",
    )
    phosphorus: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available phosphorus concentration in mg/kg (ppm)",
    )
    potassium: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Available potassium concentration in mg/kg (ppm)",
    )
    notes: str | None = Field(
        default=None,
        description="Free-text agronomist observations or lab report references",
    )


class SoilProfileResponse(SoilProfileBase):
    """
    Outbound representation of a SoilProfile returned to API consumers.

    Extends SoilProfileBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the soil profile record")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
