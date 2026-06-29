"""Crop domain factory."""

from __future__ import annotations

from datetime import date

from app.cdd.context import GenerationContext
from app.cdd.types import CDDCropRecord, CDDFieldRecord
from app.db.models.crop import CropStatus


def _resolve_status(
    planting_date: date,
    expected_harvest_date: date,
    reference: date,
) -> CropStatus:
    if reference < planting_date:
        return CropStatus.PLANNED
    if reference < expected_harvest_date:
        return CropStatus.GROWING
    return CropStatus.HARVESTED


def _growth_stage_for_date(
    planting_date: date,
    expected_harvest_date: date,
    reference: date,
) -> str | None:
    if reference < planting_date:
        return None
    cycle = max(1, (expected_harvest_date - planting_date).days)
    elapsed = (reference - planting_date).days
    fraction = elapsed / cycle
    if fraction < 0.15:
        return "BBCH-12"
    if fraction < 0.40:
        return "BBCH-30"
    if fraction < 0.65:
        return "BBCH-51"
    if fraction < 0.85:
        return "BBCH-69"
    if fraction < 0.95:
        return "BBCH-87"
    return "BBCH-99"


class CropFactory:
    """Generates crop rotation records from manifest entries."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
    ) -> list[CDDCropRecord]:
        field_by_code = {f.field_code: f for f in fields}
        crops: list[CDDCropRecord] = []
        reference = ctx.temporal_end.date()

        for ordinal, rotation in enumerate(ctx.manifest.crop_rotations, start=1):
            field = field_by_code[rotation.field_code]
            status = _resolve_status(
                rotation.planting_date,
                rotation.expected_harvest_date,
                reference,
            )
            actual_harvest = (
                rotation.expected_harvest_date if status == CropStatus.HARVESTED else None
            )
            actual_yield = (
                rotation.expected_yield_tons_ha
                if status == CropStatus.HARVESTED
                else None
            )

            crops.append(
                CDDCropRecord(
                    id=ctx.uuid_generator.generate_scoped(
                        "crop", rotation.field_code, ordinal
                    ),
                    field_id=field.id,
                    field_code=rotation.field_code,
                    crop_name=rotation.crop_name,
                    crop_variety=rotation.crop_variety,
                    planting_date=rotation.planting_date,
                    expected_harvest_date=rotation.expected_harvest_date,
                    actual_harvest_date=actual_harvest,
                    status=status,
                    expected_yield_tons_ha=rotation.expected_yield_tons_ha,
                    actual_yield_tons_ha=actual_yield,
                    seeding_rate_kg_ha=rotation.seeding_rate_kg_ha,
                    growth_stage=_growth_stage_for_date(
                        rotation.planting_date,
                        rotation.expected_harvest_date,
                        reference,
                    ),
                    is_perennial=rotation.is_perennial,
                    is_susceptible_to_disease=rotation.is_susceptible_to_disease,
                )
            )

        return crops
