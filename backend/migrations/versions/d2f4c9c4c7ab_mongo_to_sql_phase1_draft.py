"""Draft: Mongo -> SQL phase 1 tables (favorites/messages/support)

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
depends_on = None


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

    # Message Threads
    op.create_table(
        "message_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("listing_title", sa.String(length=255), nullable=True),
        sa.Column("listing_image", sa.String(length=500), nullable=True),
        sa.Column("last_message", sa.Text(), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_threads_listing", "message_threads", ["listing_id"], unique=False)
    op.create_index("ix_message_threads_last_message", "message_threads", ["last_message_at"], unique=False)

    # Message Thread Participants
    op.create_table(
        "message_thread_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("message_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("unread_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_message_thread_participants_thread", "message_thread_participants", ["thread_id"], unique=False)
    op.create_index("ix_message_thread_participants_user", "message_thread_participants", ["user_id"], unique=False)
    op.create_index("ix_message_thread_participant_unique", "message_thread_participants", ["thread_id", "user_id"], unique=True)

    # Messages
    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("thread_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("message_threads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("client_message_id", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_thread", "messages", ["thread_id"], unique=False)
    op.create_index("ix_messages_sender", "messages", ["sender_id"], unique=False)
    op.create_index("ix_messages_thread_created", "messages", ["thread_id", "created_at"], unique=False)
    op.create_index("ix_messages_idempotent", "messages", ["thread_id", "sender_id", "client_message_id"], unique=True)

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

    op.drop_index("ix_messages_idempotent", table_name="messages")
    op.drop_index("ix_messages_thread_created", table_name="messages")
    op.drop_index("ix_messages_sender", table_name="messages")
    op.drop_index("ix_messages_thread", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_message_thread_participant_unique", table_name="message_thread_participants")
    op.drop_index("ix_message_thread_participants_user", table_name="message_thread_participants")
    op.drop_index("ix_message_thread_participants_thread", table_name="message_thread_participants")
    op.drop_table("message_thread_participants")

    op.drop_index("ix_message_threads_last_message", table_name="message_threads")
    op.drop_index("ix_message_threads_listing", table_name="message_threads")
    op.drop_table("message_threads")

    op.drop_index("ix_favorites_user_listing", table_name="favorites")
    op.drop_index("ix_favorites_listing_id", table_name="favorites")
    op.drop_index("ix_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
