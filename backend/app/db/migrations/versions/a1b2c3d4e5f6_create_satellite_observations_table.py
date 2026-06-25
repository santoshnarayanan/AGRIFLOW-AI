"""create satellite_observations table

Revision ID: a1b2c3d4e5f6
Revises: d3e7b2a9f1c4
Create Date: 2026-06-25 12:00:00.000000

Creates the satellite_observations table — Phase 11 of AGRIFLOW-AI.
SatelliteObservation is a direct child of Field:

    Farm → Field → SatelliteObservation

Unlike YieldRecord and DiseaseObservation (Phase 9/10), which anchor on
Crop because those measurements are per-crop-cycle, SatelliteObservation
anchors directly on Field.  Satellite imagery is captured at the field level
independently of any specific crop cycle — the closest analogues are
SensorReading (Phase 7) and IrrigationEvent (Phase 8).

Notable DDL decisions
---------------------
- Three named PostgreSQL ENUM types are created before the table:
    ``satellite_provider`` — imagery source platform
      (SENTINEL_2, LANDSAT_8, LANDSAT_9, PLANET, MODIS, SPOT, WORLDVIEW, UNKNOWN)
    ``spectral_index``     — derived vegetation/water index type
      (NDVI, EVI, NDWI, SAVI, NDRE, LAI, MSAVI, GNDVI)
    ``processing_level``   — data processing tier
      (L1C, L2A, ARD, DERIVED)
  All three are dropped explicitly in downgrade() because PostgreSQL does NOT
  automatically drop named enum types when the owning table is removed.
- postgresql.ENUM with create_type=False is used for all three enums so that
  op.create_table() does not emit a second CREATE TYPE.  The type lifecycle is
  owned entirely by the .create() / .drop() calls — see migration a8f3d1b6e924
  for the full rationale (sa.Enum._copy() does not forward create_type=False in
  SQLAlchemy 2.0.x).
- ``observed_at`` is the primary time key: TIMESTAMPTZ NOT NULL, individually
  indexed, and included in the compound index with field_id.  It is the
  partition key for a future TimescaleDB hypertable promotion (Phase 12).
- ``index_value`` is stored as NUMERIC(9, 6) to avoid IEEE-754 accumulation
  errors in aggregate time-series queries.  Spectral indices are dimensionless
  ratios: NDVI/EVI/NDWI/SAVI/NDRE/MSAVI/GNDVI are bounded to [-1, 1];
  LAI can reach ~10 in dense tropical canopies.  The 9,6 precision covers
  this full range with six decimal places.
- One FK constraint with ON DELETE CASCADE is declared:
    fk_satellite_observations_field_id — domain anchor (field-level data)
  This is consistent with all other Field-child migrations (SensorReading,
  IrrigationEvent).  Deleting a Field removes all its satellite observations.
- Seven indexes cover the dominant access patterns:
    1. ix_satellite_observations_field_id             — "all observations for a field"
    2. ix_satellite_observations_observed_at          — "observations in a time window"
    3. ix_satellite_observations_satellite_provider   — "AI training data filter by provider"
    4. ix_satellite_observations_spectral_index       — "filter by index type"
    5. ix_satellite_observations_scene_id             — "provenance / deduplication lookup"
    6. ix_satellite_observations_field_id_observed_at — "field observations in time order"
    7. ix_satellite_observations_spectral_index_observed_at — "index-specific time series"
  Indexes 6 and 7 are the primary compound access patterns for field history
  queries and the Phase 12–14 AI feature extraction pipelines.
- This migration is structurally forward-compatible with TimescaleDB hypertable
  promotion (partition by ``observed_at``) and Cassandra migration (partition
  by ``field_id``, cluster by ``observed_at``).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "d3e7b2a9f1c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# postgresql.ENUM (not sa.Enum) is used here intentionally.
# sa.Enum._copy() — called internally by op.create_table() when the type is
# cloned into the temporary Table object — does not forward create_type=False
# in SQLAlchemy 2.0.x, causing a DuplicateObjectError on fresh databases.
# postgresql.ENUM preserves create_type=False through _set_table() and _copy()
# so op.create_table() emits no DDL for these types.
satellite_provider_enum = postgresql.ENUM(
    "SENTINEL_2",
    "LANDSAT_8",
    "LANDSAT_9",
    "PLANET",
    "MODIS",
    "SPOT",
    "WORLDVIEW",
    "UNKNOWN",
    name="satellite_provider",
    create_type=False,
)

spectral_index_enum = postgresql.ENUM(
    "NDVI",
    "EVI",
    "NDWI",
    "SAVI",
    "NDRE",
    "LAI",
    "MSAVI",
    "GNDVI",
    name="spectral_index",
    create_type=False,
)

processing_level_enum = postgresql.ENUM(
    "L1C",
    "L2A",
    "ARD",
    "DERIVED",
    name="processing_level",
    create_type=False,
)


def upgrade() -> None:
    # ── 1. Create PostgreSQL ENUM types ─────────────────────────────────────
    # Must exist before the table that references them.  create_type=False on
    # the enum objects above ensures op.create_table() does not emit a second
    # CREATE TYPE for any of the three types.
    satellite_provider_enum.create(op.get_bind(), checkfirst=True)
    spectral_index_enum.create(op.get_bind(), checkfirst=True)
    processing_level_enum.create(op.get_bind(), checkfirst=True)

    # ── 2. Create the satellite_observations table ───────────────────────────
    op.create_table(
        "satellite_observations",
        # ── Primary key ───────────────────────────────────────────────────────
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="UUID v4 primary key",
        ),
        # ── Foreign key ───────────────────────────────────────────────────────
        sa.Column(
            "field_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            comment=(
                "Field this satellite observation belongs to; "
                "primary domain anchor — satellite imagery is field-level, "
                "not crop-cycle-level"
            ),
        ),
        # ── Observation timestamp ─────────────────────────────────────────────
        sa.Column(
            "observed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            comment=(
                "Timezone-aware timestamp of the satellite overpass; "
                "serves as the primary time key and TimescaleDB partition key"
            ),
        ),
        # ── Source classification ─────────────────────────────────────────────
        sa.Column(
            "satellite_provider",
            satellite_provider_enum,
            nullable=False,
            comment=(
                "Satellite platform or data provider that sourced the imagery; "
                "used as a spatial-resolution quality weight in AI training pipelines"
            ),
        ),
        sa.Column(
            "processing_level",
            processing_level_enum,
            nullable=False,
            comment=(
                "Processing tier of the source data before index computation; "
                "ARD and L2A are required for multi-temporal AI training features; "
                "L1C observations are stored but down-weighted or excluded from "
                "model training by the feature engineering pipeline"
            ),
        ),
        # ── Spectral measurement ──────────────────────────────────────────────
        sa.Column(
            "spectral_index",
            spectral_index_enum,
            nullable=False,
            comment=(
                "Derived spectral or vegetation index type; "
                "primary measurement discriminator — the satellite equivalent of SensorType"
            ),
        ),
        sa.Column(
            "index_value",
            sa.Numeric(precision=9, scale=6),
            nullable=False,
            comment=(
                "Computed index value; typical ranges: "
                "NDVI/EVI/NDWI/SAVI/NDRE/MSAVI/GNDVI [-1.0, 1.0], "
                "LAI [0, ~10]; "
                "stored as NUMERIC to avoid IEEE-754 accumulation errors in "
                "aggregate and time-series queries"
            ),
        ),
        # ── Image quality metadata ────────────────────────────────────────────
        sa.Column(
            "cloud_cover_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
            comment=(
                "Percentage of the scene covered by cloud or cloud shadow; "
                "valid range [0, 100]; "
                "feature pipelines should filter observations above the "
                "project-standard threshold (typically 20 %) before AI training"
            ),
        ),
        sa.Column(
            "resolution_m",
            sa.Numeric(precision=8, scale=2),
            nullable=True,
            comment=(
                "Effective pixel resolution of the source imagery in metres; "
                "e.g. 10.0 (Sentinel-2), 30.0 (Landsat), 3.0 (Planet), 250.0 (MODIS); "
                "used as a quality weight in spatial feature engineering"
            ),
        ),
        # ── Provenance ────────────────────────────────────────────────────────
        sa.Column(
            "scene_id",
            sa.String(255),
            nullable=True,
            comment=(
                "Provider-assigned scene or tile identifier; "
                "enables traceability back to the original imagery source, "
                "e.g. 'S2A_MSIL2A_20240615T102021_N0510_R065_T32UMD_20240615T130512'"
            ),
        ),
        sa.Column(
            "source_url",
            sa.String(500),
            nullable=True,
            comment=(
                "URL or cloud storage path to the source Cloud Optimised GeoTIFF (COG) "
                "or derived product; supports ingestion pipeline traceability "
                "and reprocessing workflows"
            ),
        ),
        # ── Operator metadata ─────────────────────────────────────────────────
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment=(
                "Operator or pipeline free-text annotations, "
                "e.g. reprocessing notes, known image artefacts, or calibration flags"
            ),
        ),
        # ── Audit timestamps (server-side) ────────────────────────────────────
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row creation timestamp (set by PostgreSQL)",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row last-updated timestamp (set by PostgreSQL)",
        ),
        # ── Table-level constraints ───────────────────────────────────────────
        sa.ForeignKeyConstraint(
            ["field_id"],
            ["fields.id"],
            name="fk_satellite_observations_field_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_satellite_observations"),
    )

    # ── 3. Individual B-tree indexes ──────────────────────────────────────────
    # Each covers a single-column predicate used in list and filter queries.
    # op.f() is used for single-column indexes so Alembic's naming convention
    # is applied consistently across the schema.
    op.create_index(
        op.f("ix_satellite_observations_field_id"),
        "satellite_observations",
        ["field_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_satellite_observations_observed_at"),
        "satellite_observations",
        ["observed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_satellite_observations_satellite_provider"),
        "satellite_observations",
        ["satellite_provider"],
        unique=False,
    )
    op.create_index(
        op.f("ix_satellite_observations_spectral_index"),
        "satellite_observations",
        ["spectral_index"],
        unique=False,
    )
    op.create_index(
        op.f("ix_satellite_observations_scene_id"),
        "satellite_observations",
        ["scene_id"],
        unique=False,
    )

    # ── 4. Compound B-tree indexes ────────────────────────────────────────────
    # Primary access patterns for field history queries and the Phase 12–14
    # AI feature extraction pipelines.  Named explicitly (without op.f()) to
    # match the compound index names defined in the ORM __table_args__.
    op.create_index(
        "ix_satellite_observations_field_id_observed_at",
        "satellite_observations",
        ["field_id", "observed_at"],
        unique=False,
    )
    op.create_index(
        "ix_satellite_observations_spectral_index_observed_at",
        "satellite_observations",
        ["spectral_index", "observed_at"],
        unique=False,
    )


def downgrade() -> None:
    # Reverse order: compound indexes → individual indexes → table → enum types.
    # ForeignKeyConstraint and PrimaryKeyConstraint are dropped automatically
    # when the table is removed.

    # ── Compound indexes ──────────────────────────────────────────────────────
    op.drop_index(
        "ix_satellite_observations_spectral_index_observed_at",
        table_name="satellite_observations",
    )
    op.drop_index(
        "ix_satellite_observations_field_id_observed_at",
        table_name="satellite_observations",
    )

    # ── Individual indexes ────────────────────────────────────────────────────
    op.drop_index(
        op.f("ix_satellite_observations_scene_id"),
        table_name="satellite_observations",
    )
    op.drop_index(
        op.f("ix_satellite_observations_spectral_index"),
        table_name="satellite_observations",
    )
    op.drop_index(
        op.f("ix_satellite_observations_satellite_provider"),
        table_name="satellite_observations",
    )
    op.drop_index(
        op.f("ix_satellite_observations_observed_at"),
        table_name="satellite_observations",
    )
    op.drop_index(
        op.f("ix_satellite_observations_field_id"),
        table_name="satellite_observations",
    )

    # ── Table ─────────────────────────────────────────────────────────────────
    op.drop_table("satellite_observations")

    # ── Enum types ────────────────────────────────────────────────────────────
    # PostgreSQL retains named enum types after the owning table is dropped;
    # explicit removal is required to leave no orphan types in the schema.
    # Dropped in reverse creation order.  .drop() is symmetric with .create()
    # in upgrade().
    processing_level_enum.drop(op.get_bind(), checkfirst=False)
    spectral_index_enum.drop(op.get_bind(), checkfirst=False)
    satellite_provider_enum.drop(op.get_bind(), checkfirst=False)
