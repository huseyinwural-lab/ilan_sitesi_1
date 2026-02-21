"""Draft: Mongo -> SQL phase 1 tables (favorites/support)

Revision ID: d2f4c9c4c7ab
Revises: 9ccf26034bea
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d2f4c9c4c7ab"
down_revision = "9ccf26034bea"
branch_labels = None
depends_on = "p20_applications_table"


def upgrade() -> None:
    # Favorites
    op.create_table(
        "favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_favorites_user_id", "favorites", ["user_id"], unique=False)
    op.create_index("ix_favorites_listing_id", "favorites", ["listing_id"], unique=False)
    op.create_index("ix_favorites_user_listing", "favorites", ["user_id", "listing_id"], unique=True)

    # Support Messages (for Applications)
    op.create_table(
        "support_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_support_messages_application", "support_messages", ["application_id", "created_at"], unique=False)
    op.create_index("ix_support_messages_sender", "support_messages", ["sender_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_support_messages_sender", table_name="support_messages")
    op.drop_index("ix_support_messages_application", table_name="support_messages")
    op.drop_table("support_messages")

    op.drop_index("ix_favorites_user_listing", table_name="favorites")
    op.drop_index("ix_favorites_listing_id", table_name="favorites")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
