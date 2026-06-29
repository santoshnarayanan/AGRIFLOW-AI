"""Field domain factory."""

from __future__ import annotations

from app.cdd.context import GenerationContext
from app.cdd.types import CDDFarmRecord, CDDFieldRecord


class FieldFactory:
    """Generates field entities for the demonstration farm."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        farms: list[CDDFarmRecord],
    ) -> list[CDDFieldRecord]:
        if not farms:
            return []

        farm = farms[0]
        fields: list[CDDFieldRecord] = []

        for ordinal, field_def in enumerate(ctx.manifest.fields, start=1):
            fields.append(
                CDDFieldRecord(
                    id=ctx.uuid_generator.generate("field", field_def.field_code),
                    farm_id=farm.id,
                    field_code=field_def.field_code,
                    name=field_def.name,
                    area_hectares=field_def.area_hectares,
                    soil_type=field_def.soil_texture_label,
                    latitude=farm.latitude + field_def.latitude_offset,
                    longitude=farm.longitude + field_def.longitude_offset,
                    elevation_m=field_def.elevation_m,
                    irrigation_method=field_def.irrigation_method,
                    is_irrigated=field_def.is_irrigated,
                )
            )

        return fields
