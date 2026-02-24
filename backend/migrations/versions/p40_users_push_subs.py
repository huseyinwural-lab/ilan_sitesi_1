"""
P40: extend users + add push_subscriptions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p40_users_push_subs'
down_revision: Union[str, Sequence[str], None] = 'p39_users_listings_cutover'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "users" in inspector.get_table_names():
        cols = _column_names(inspector, "users")
        if "first_name" not in cols:
            op.add_column("users", sa.Column("first_name", sa.String(length=120), nullable=True))
        if "last_name" not in cols:
            op.add_column("users", sa.Column("last_name", sa.String(length=120), nullable=True))
        if "status" not in cols:
            op.add_column("users", sa.Column("status", sa.String(length=20), nullable=False, server_default="active"))
        if "dealer_status" not in cols:
            op.add_column("users", sa.Column("dealer_status", sa.String(length=20), nullable=True))
        if "suspension_until" not in cols:
            op.add_column("users", sa.Column("suspension_until", sa.DateTime(timezone=True), nullable=True))
        if "deleted_at" not in cols:
            op.add_column("users", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        if "phone_e164" not in cols:
            op.add_column("users", sa.Column("phone_e164", sa.String(length=40), nullable=True))
        if "notification_prefs" not in cols:
            op.add_column(
                "users",
                sa.Column("notification_prefs", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            )
        if "plan_id" not in cols:
            op.add_column("users", sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key("fk_users_plan_id", "users", "plans", ["plan_id"], ["id"])
        if "plan_expires_at" not in cols:
            op.add_column("users", sa.Column("plan_expires_at", sa.DateTime(timezone=True), nullable=True))

    if "push_subscriptions" not in inspector.get_table_names():
        op.create_table(
            "push_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("endpoint", sa.Text(), nullable=False),
            sa.Column("p256dh", sa.Text(), nullable=False),
            sa.Column("auth", sa.Text(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("revoked_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_push_subscriptions_user", "push_subscriptions", ["user_id"])
        op.create_index("ix_push_subscriptions_active", "push_subscriptions", ["is_active"])
        op.create_index("ix_push_subscriptions_endpoint", "push_subscriptions", ["endpoint"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "push_subscriptions" in inspector.get_table_names():
        op.drop_index("ix_push_subscriptions_endpoint", table_name="push_subscriptions")
        op.drop_index("ix_push_subscriptions_active", table_name="push_subscriptions")
        op.drop_index("ix_push_subscriptions_user", table_name="push_subscriptions")
        op.drop_table("push_subscriptions")

    if "users" in inspector.get_table_names():
        cols = _column_names(inspector, "users")
        if "plan_id" in cols:
            op.drop_constraint("fk_users_plan_id", "users", type_="foreignkey")
        for column_name in (
            "plan_expires_at",
            "plan_id",
            "notification_prefs",
            "phone_e164",
            "deleted_at",
            "suspension_until",
            "dealer_status",
            "status",
            "last_name",
            "first_name",
        ):
            if column_name in cols:
                op.drop_column("users", column_name)
