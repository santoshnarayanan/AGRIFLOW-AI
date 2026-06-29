"""Farm domain factory."""

from __future__ import annotations

from app.cdd.context import GenerationContext
from app.cdd.types import CDDFarmRecord


class FarmFactory:
    """Generates the root farm aggregate for the CDD."""

    @staticmethod
    def generate(ctx: GenerationContext) -> list[CDDFarmRecord]:
        farm_def = ctx.manifest.farm
        total_area = sum(f.area_hectares for f in ctx.manifest.fields)

        farm = CDDFarmRecord(
            id=ctx.uuid_generator.generate("farm", farm_def.farm_code),
            farm_code=farm_def.farm_code,
            farm_name=farm_def.farm_name,
            owner_name=farm_def.owner_name,
            country=farm_def.country,
            state=farm_def.state,
            city=farm_def.city,
            latitude=farm_def.latitude,
            longitude=farm_def.longitude,
            total_area_hectares=total_area,
            is_active=True,
        )
        return [farm]
