"""add notifications table v1

Revision ID: 5710cb21ddfd
Revises: p28_email_verification_fields
Create Date: 2026-02-21 16:26:10.211664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5710cb21ddfd'
down_revision: Union[str, Sequence[str], None] = 'p28_email_verification_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("action_url", sa.String(), nullable=True),
        sa.Column("payload_json", sa.JSON(), nullable=True),
        sa.Column("dedupe_key", sa.String(), nullable=True),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_notifications_user_created", "notifications", ["user_id", "created_at"])
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "read_at"])
    op.create_index(
        "ix_notifications_user_dedupe",
        "notifications",
        ["user_id", "dedupe_key"],
        unique=True,
    )
    op.create_index("ix_notifications_source", "notifications", ["source_type", "source_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_source", table_name="notifications")
    op.drop_index("ix_notifications_user_dedupe", table_name="notifications")
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_notifications_user_created", table_name="notifications")
    op.drop_table("notifications")
