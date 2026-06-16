"""
Pydantic schemas for the Crop domain object.

Separation of concerns
----------------------
- CropBase      — shared field inventory; acts as the parent of CropResponse.
- CropCreate    — inbound payload for POST.  Contains only the four fields a
                  caller supplies at creation time.  ``actual_harvest_date``
                  and ``status`` are intentionally excluded: status is
                  initialised to PLANNED by the service layer, and
                  actual_harvest_date is only recorded at harvest completion.
                  ``field_id`` comes from the URL path, not the request body.
- CropUpdate    — inbound payload for PATCH.  Every field is optional so
                  callers can send a sparse partial update.
- CropResponse  — outbound representation returned to API consumers.  Inherits
                  CropBase and adds the server-assigned fields (id, field_id,
                  created_at, updated_at).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.crop import CropStatus


class CropBase(BaseModel):
    """
    Shared field inventory for the Crop domain.

    Inherited by CropResponse.  CropUpdate mirrors these fields but marks all
    of them optional, so it is defined separately rather than as a subclass.
    """

    crop_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Common or scientific crop name, e.g. 'Maize', 'Solanum lycopersicum'",
    )
    crop_variety: str | None = Field(
        default=None,
        max_length=255,
        description="Cultivar or hybrid designation, e.g. 'DKC 6870'",
    )
    planting_date: date = Field(
        ...,
        description="Calendar date the crop was or will be planted (ISO 8601, e.g. 2026-03-15)",
    )
    expected_harvest_date: date | None = Field(
        default=None,
        description="Agronomically projected harvest date",
    )
    actual_harvest_date: date | None = Field(
        default=None,
        description="Actual harvest completion date; populated only when status = HARVESTED",
    )
    status: CropStatus = Field(
        default=CropStatus.PLANNED,
        description="Current agronomic lifecycle state (PLANNED → PLANTED → GROWING → HARVESTED)",
    )

    # ── AI data (P1 — Yield Prediction) ──────────────────────────────────────
    actual_yield_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Actual yield at harvest in tonnes per hectare; populated only when status = HARVESTED",
    )
    expected_yield_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Agronomist or AI-projected yield target in tonnes per hectare",
    )
    seeding_rate_kg_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Seeding density at planting in kg per hectare",
    )
    growth_stage: str | None = Field(
        default=None,
        max_length=20,
        description="BBCH phenological growth stage code, e.g. 'BBCH-59'",
    )


class CropCreate(BaseModel):
    """
    Request body for POST /fields/{field_id}/crops.

    Only the four fields a caller can meaningfully supply at creation time are
    exposed here.  The remaining fields are either server-managed (status
    defaults to PLANNED) or recorded later in the lifecycle (actual_harvest_date).
    """

    crop_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Common or scientific crop name, e.g. 'Maize', 'Solanum lycopersicum'",
    )
    crop_variety: str | None = Field(
        default=None,
        max_length=255,
        description="Cultivar or hybrid designation, e.g. 'DKC 6870'",
    )
    planting_date: date = Field(
        ...,
        description="Calendar date the crop was or will be planted (ISO 8601, e.g. 2026-03-15)",
    )
    expected_harvest_date: date | None = Field(
        default=None,
        description="Agronomically projected harvest date",
    )

    # ── AI data (P1 — Yield Prediction) ──────────────────────────────────────
    # actual_yield_tons_ha is intentionally excluded from CropCreate.
    # Yield is a harvest-time observation recorded via PATCH once the crop
    # reaches HARVESTED status, following the same pattern as actual_harvest_date.
    expected_yield_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Agronomist or AI-projected yield target in tonnes per hectare",
    )
    seeding_rate_kg_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Seeding density at planting in kg per hectare",
    )
    growth_stage: str | None = Field(
        default=None,
        max_length=20,
        description="BBCH phenological growth stage code, e.g. 'BBCH-59'",
    )


class CropUpdate(BaseModel):
    """
    Request body for PATCH /fields/{field_id}/crops/{crop_id}.

    All fields are optional to support sparse partial updates.  The service
    layer is responsible for validating state-machine transitions when
    ``status`` or ``actual_harvest_date`` are included.
    """

    crop_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Common or scientific crop name",
    )
    crop_variety: str | None = Field(
        default=None,
        max_length=255,
        description="Cultivar or hybrid designation",
    )
    planting_date: date | None = Field(
        default=None,
        description="Calendar date the crop was or will be planted",
    )
    expected_harvest_date: date | None = Field(
        default=None,
        description="Agronomically projected harvest date",
    )
    actual_harvest_date: date | None = Field(
        default=None,
        description="Actual harvest completion date; set only when transitioning to HARVESTED",
    )
    status: CropStatus | None = Field(
        default=None,
        description="Target agronomic lifecycle state",
    )

    # ── AI data (P1 — Yield Prediction) ──────────────────────────────────────
    actual_yield_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Actual yield at harvest in tonnes per hectare; set when status transitions to HARVESTED",
    )
    expected_yield_tons_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
        description="Agronomist or AI-projected yield target in tonnes per hectare",
    )
    seeding_rate_kg_ha: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=3,
        description="Seeding density at planting in kg per hectare",
    )
    growth_stage: str | None = Field(
        default=None,
        max_length=20,
        description="BBCH phenological growth stage code, e.g. 'BBCH-59'",
    )


class CropResponse(CropBase):
    """
    Outbound representation of a Crop returned to API consumers.

    Extends CropBase with server-assigned identity and audit fields.
    ``from_attributes=True`` enables direct construction from a SQLAlchemy
    ORM instance without a manual mapping step.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="UUID v4 primary key of the crop record")
    field_id: uuid.UUID = Field(description="UUID of the parent field")
    created_at: datetime = Field(description="Row creation timestamp (UTC)")
    updated_at: datetime = Field(description="Row last-updated timestamp (UTC)")
