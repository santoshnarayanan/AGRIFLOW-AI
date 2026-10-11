"""create domain_event_consumer_inbox table

Phase 14 — consumer idempotency ledger.

Revision ID: j4k5l6m7n8o9
Revises: i3j4k5l6m7n8
Create Date: 2026-10-11
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "j4k5l6m7n8o9"
down_revision: str = "i3j4k5l6m7n8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "domain_event_consumer_inbox",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("consumer_group_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "event_id",
            "consumer_group_id",
            name="uq_domain_event_consumer_inbox_event_group",
        ),
    )
    op.create_index(
        "ix_domain_event_consumer_inbox_event_id",
        "domain_event_consumer_inbox",
        ["event_id"],
    )
    op.create_index(
        "ix_domain_event_consumer_inbox_consumer_group_id",
        "domain_event_consumer_inbox",
        ["consumer_group_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_domain_event_consumer_inbox_consumer_group_id",
        table_name="domain_event_consumer_inbox",
    )
    op.drop_index(
        "ix_domain_event_consumer_inbox_event_id",
        table_name="domain_event_consumer_inbox",
    )
    op.drop_table("domain_event_consumer_inbox")
