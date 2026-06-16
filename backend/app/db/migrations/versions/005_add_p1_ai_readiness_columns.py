"""add P1 AI readiness columns

Revision ID: f3a8c1d9e047
Revises: 7d4f2a9b1e63
Create Date: 2026-06-16 22:00:00.000000

Adds all Priority 1 (Yield Prediction MVP) columns identified in the
AI Data Readiness Assessment (docs/AI_DATA_READINESS_ASSESSMENT.md).

All columns across all four tables are:
- NULLABLE with no server_default
- Added via ADD COLUMN — instantaneous DDL on PostgreSQL 11+ (metadata-only)
- Fully reversible via DROP COLUMN in downgrade()

Tables modified
---------------
crops
    actual_yield_tons_ha       NUMERIC(10, 4)  — harvest yield target variable
    expected_yield_tons_ha     NUMERIC(10, 4)  — agronomist yield benchmark
    seeding_rate_kg_ha         NUMERIC(8, 3)   — planting density input
    growth_stage               VARCHAR(20)     — BBCH phenological stage code

weather_records
    solar_radiation_wm2        NUMERIC(8, 3)   — Penman-Monteith ET₀ input
    temperature_min_c          NUMERIC(5, 2)   — GDD calculation (daily min)
    temperature_max_c          NUMERIC(5, 2)   — GDD calculation (daily max)

soil_profiles
    soil_depth_cm              NUMERIC(6, 2)   — root zone depth constraint
    cation_exchange_capacity_meq NUMERIC(8, 4) — nutrient retention capacity

fields
    elevation_m                NUMERIC(8, 2)   — topographic confound variable

Backward compatibility
----------------------
Existing rows in all four tables are unaffected — all new columns default to
NULL.  Existing API payloads that omit the new fields continue to work
unchanged.  API responses now include the new fields as null.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f3a8c1d9e047"
down_revision: Union[str, None] = "7d4f2a9b1e63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── crops ─────────────────────────────────────────────────────────────────
    op.add_column(
        "crops",
        sa.Column(
            "actual_yield_tons_ha",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment=(
                "Actual yield recorded at harvest in tonnes per hectare; "
                "populated only when status = HARVESTED"
            ),
        ),
    )
    op.add_column(
        "crops",
        sa.Column(
            "expected_yield_tons_ha",
            sa.Numeric(precision=10, scale=4),
            nullable=True,
            comment="Agronomist or AI-projected yield target in tonnes per hectare",
        ),
    )
    op.add_column(
        "crops",
        sa.Column(
            "seeding_rate_kg_ha",
            sa.Numeric(precision=8, scale=3),
            nullable=True,
            comment="Seeding density at planting in kg per hectare",
        ),
    )
    op.add_column(
        "crops",
        sa.Column(
            "growth_stage",
            sa.String(20),
            nullable=True,
            comment="Current BBCH phenological growth stage code, e.g. 'BBCH-59'",
        ),
    )

    # ── weather_records ───────────────────────────────────────────────────────
    op.add_column(
        "weather_records",
        sa.Column(
            "solar_radiation_wm2",
            sa.Numeric(precision=8, scale=3),
            nullable=True,
            comment="Solar irradiance in W/m²; required for Penman-Monteith ET₀ calculation",
        ),
    )
    op.add_column(
        "weather_records",
        sa.Column(
            "temperature_min_c",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment="Daily minimum air temperature in °C; used for Growing Degree Day calculation",
        ),
    )
    op.add_column(
        "weather_records",
        sa.Column(
            "temperature_max_c",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment="Daily maximum air temperature in °C; used for Growing Degree Day calculation",
        ),
    )

    # ── soil_profiles ─────────────────────────────────────────────────────────
    op.add_column(
        "soil_profiles",
        sa.Column(
            "soil_depth_cm",
            sa.Numeric(precision=6, scale=2),
            nullable=True,
            comment="Effective rooting zone depth in centimetres",
        ),
    )
    op.add_column(
        "soil_profiles",
        sa.Column(
            "cation_exchange_capacity_meq",
            sa.Numeric(precision=8, scale=4),
            nullable=True,
            comment="Cation exchange capacity in meq/100g; indicates soil nutrient retention",
        ),
    )

    # ── fields ────────────────────────────────────────────────────────────────
    op.add_column(
        "fields",
        sa.Column(
            "elevation_m",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
            comment=(
                "Field elevation in metres above sea level; "
                "negative values valid (e.g. fields below sea level)"
            ),
        ),
    )


def downgrade() -> None:
    # Reverse order: fields → soil_profiles → weather_records → crops
    # (mirrors the domain hierarchy; no FK dependencies between these columns)

    # ── fields ────────────────────────────────────────────────────────────────
    op.drop_column("fields", "elevation_m")

    # ── soil_profiles ─────────────────────────────────────────────────────────
    op.drop_column("soil_profiles", "cation_exchange_capacity_meq")
    op.drop_column("soil_profiles", "soil_depth_cm")

    # ── weather_records ───────────────────────────────────────────────────────
    op.drop_column("weather_records", "temperature_max_c")
    op.drop_column("weather_records", "temperature_min_c")
    op.drop_column("weather_records", "solar_radiation_wm2")

    # ── crops ─────────────────────────────────────────────────────────────────
    op.drop_column("crops", "growth_stage")
    op.drop_column("crops", "seeding_rate_kg_ha")
    op.drop_column("crops", "expected_yield_tons_ha")
    op.drop_column("crops", "actual_yield_tons_ha")
