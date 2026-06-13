"""add soil profiles table

Revision ID: 13aabbe35d51
Revises: 5c2d8e3f7a19
Create Date: 2026-06-13 19:42:40.995187
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '13aabbe35d51'
down_revision: Union[str, None] = '5c2d8e3f7a19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "soil_profiles",
        sa.Column(
            "field_id",
            sa.UUID(),
            nullable=False,
            comment="Parent field this soil profile belongs to (one-to-one)",
        ),
        sa.Column(
            "soil_type",
            sa.Enum(
                "SANDY",
                "CLAY",
                "LOAM",
                "SILT",
                "PEAT",
                "CHALK",
                name="soil_type",
                create_constraint=True,
            ),
            nullable=False,
            comment="Dominant soil texture classification",
        ),
        sa.Column(
            "ph",
            sa.Numeric(precision=4, scale=2),
            nullable=True,
            comment="Soil pH on the 0–14 scale; 7.0 is neutral",
        ),
        sa.Column(
            "organic_matter",
            sa.Numeric(precision=6, scale=3),
            nullable=True,
            comment="Organic matter content as a percentage by weight",
        ),
        sa.Column(
            "nitrogen",
            sa.Numeric(precision=8, scale=4),
            nullable=True,
            comment="Total nitrogen concentration in mg/kg (ppm)",
        ),
        sa.Column(
            "phosphorus",
            sa.Numeric(precision=8, scale=4),
            nullable=True,
            comment="Available phosphorus concentration in mg/kg (ppm)",
        ),
        sa.Column(
            "potassium",
            sa.Numeric(precision=8, scale=4),
            nullable=True,
            comment="Available potassium concentration in mg/kg (ppm)",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Free-text agronomist observations or lab report references",
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["field_id"], ["fields.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        op.f("ix_soil_profiles_field_id"),
        "soil_profiles",
        ["field_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_soil_profiles_field_id"),
        table_name="soil_profiles",
    )
    op.drop_table("soil_profiles")
    # ### end Alembic commands ###
