"""webhook event log

Revision ID: c5833a1fffde
Revises: 61b7aaac3b55
Create Date: 2026-02-21 19:04:28.375277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5833a1fffde'
down_revision: Union[str, Sequence[str], None] = '61b7aaac3b55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "webhook_event_logs",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=20), nullable=False, server_default="stripe"),
        sa.Column("event_id", sa.String(length=120), nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="received"),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("signature_valid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("error_message", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_webhook_event_provider_event",
        "webhook_event_logs",
        ["provider", "event_id"],
    )
    op.create_index("ix_webhook_event_created", "webhook_event_logs", ["created_at"])
    op.create_index("ix_webhook_event_status", "webhook_event_logs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_webhook_event_status", table_name="webhook_event_logs")
    op.drop_index("ix_webhook_event_created", table_name="webhook_event_logs")
    op.drop_constraint("uq_webhook_event_provider_event", "webhook_event_logs", type_="unique")
    op.drop_table("webhook_event_logs")
