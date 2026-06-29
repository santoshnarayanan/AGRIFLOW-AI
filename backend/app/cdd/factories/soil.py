"""Soil profile domain factory."""

from __future__ import annotations

from app.cdd.context import GenerationContext
from app.cdd.correlation.engine import infiltration_rate_for_texture
from app.cdd.types import CDDFieldRecord, CDDSoilProfileRecord
from app.db.models.soil_profile import SoilType

_TEXTURE_TO_SOIL_TYPE: dict[str, SoilType] = {
    "Sandy": SoilType.SANDY,
    "Sandy Loam": SoilType.SANDY,
    "Loam": SoilType.LOAM,
    "Silt Loam": SoilType.SILT,
    "Clay Loam": SoilType.CLAY,
    "Silty Clay": SoilType.CLAY,
    "Clay": SoilType.CLAY,
}

# Deterministic nutrient baselines keyed by texture label
_SOIL_CHEMISTRY: dict[str, dict[str, float]] = {
    "Loam": {
        "ph": 6.5,
        "organic_matter": 3.8,
        "nitrogen": 28.0,
        "phosphorus": 22.0,
        "potassium": 180.0,
        "soil_depth_cm": 90.0,
        "cec": 18.5,
    },
    "Clay Loam": {
        "ph": 6.2,
        "organic_matter": 4.2,
        "nitrogen": 32.0,
        "phosphorus": 18.0,
        "potassium": 210.0,
        "soil_depth_cm": 75.0,
        "cec": 24.0,
    },
    "Silt Loam": {
        "ph": 6.8,
        "organic_matter": 3.5,
        "nitrogen": 26.0,
        "phosphorus": 25.0,
        "potassium": 165.0,
        "soil_depth_cm": 85.0,
        "cec": 16.0,
    },
    "Sandy Loam": {
        "ph": 6.0,
        "organic_matter": 2.1,
        "nitrogen": 15.0,
        "phosphorus": 12.0,
        "potassium": 95.0,
        "soil_depth_cm": 60.0,
        "cec": 10.5,
    },
    "Silty Clay": {
        "ph": 6.4,
        "organic_matter": 4.8,
        "nitrogen": 35.0,
        "phosphorus": 20.0,
        "potassium": 230.0,
        "soil_depth_cm": 70.0,
        "cec": 28.0,
    },
    "Sandy": {
        "ph": 5.8,
        "organic_matter": 1.5,
        "nitrogen": 12.0,
        "phosphorus": 10.0,
        "potassium": 80.0,
        "soil_depth_cm": 55.0,
        "cec": 8.0,
    },
    "Clay": {
        "ph": 6.1,
        "organic_matter": 3.2,
        "nitrogen": 30.0,
        "phosphorus": 16.0,
        "potassium": 200.0,
        "soil_depth_cm": 65.0,
        "cec": 26.0,
    },
}


class SoilProfileFactory:
    """Generates one soil profile per field (1:1 constraint)."""

    @staticmethod
    def generate(
        ctx: GenerationContext,
        fields: list[CDDFieldRecord],
    ) -> list[CDDSoilProfileRecord]:
        profiles: list[CDDSoilProfileRecord] = []

        for field in fields:
            texture = field.soil_type
            chemistry = _SOIL_CHEMISTRY.get(texture, _SOIL_CHEMISTRY["Loam"])
            soil_type = _TEXTURE_TO_SOIL_TYPE.get(texture, SoilType.LOAM)

            profiles.append(
                CDDSoilProfileRecord(
                    id=ctx.uuid_generator.generate_scoped(
                        "soil_profile", field.field_code, 1
                    ),
                    field_id=field.id,
                    soil_type=soil_type,
                    ph=chemistry["ph"],
                    organic_matter=chemistry["organic_matter"],
                    nitrogen=chemistry["nitrogen"],
                    phosphorus=chemistry["phosphorus"],
                    potassium=chemistry["potassium"],
                    soil_depth_cm=chemistry["soil_depth_cm"],
                    cation_exchange_capacity_meq=chemistry["cec"],
                    infiltration_rate_mm_hr=infiltration_rate_for_texture(texture),
                    notes=f"CDD synthetic profile — {texture}",
                )
            )

        return profiles
