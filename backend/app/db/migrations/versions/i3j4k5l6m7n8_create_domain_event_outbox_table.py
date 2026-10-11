"""create domain_event_outbox table

Phase 14 – Event-Driven Enterprise Platform (transactional outbox).

Revision ID: i3j4k5l6m7n8
Revises: h2i3j4k5l6m7
Create Date: 2026-10-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "i3j4k5l6m7n8"
down_revision: str = "h2i3j4k5l6m7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_event_outbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("topic", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "publish_attempts",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_domain_event_outbox_event_type",
        "domain_event_outbox",
        ["event_type"],
    )
    op.create_index(
        "ix_domain_event_outbox_aggregate_id",
        "domain_event_outbox",
        ["aggregate_id"],
    )
    op.create_index(
        "ix_domain_event_outbox_published_at",
        "domain_event_outbox",
        ["published_at"],
    )
    op.create_index(
        "ix_domain_event_outbox_pending",
        "domain_event_outbox",
        ["created_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_domain_event_outbox_pending", table_name="domain_event_outbox")
    op.drop_index("ix_domain_event_outbox_published_at", table_name="domain_event_outbox")
    op.drop_index("ix_domain_event_outbox_aggregate_id", table_name="domain_event_outbox")
    op.drop_index("ix_domain_event_outbox_event_type", table_name="domain_event_outbox")
    op.drop_table("domain_event_outbox")
