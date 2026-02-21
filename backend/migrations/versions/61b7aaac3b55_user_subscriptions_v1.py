"""user_subscriptions v1

Revision ID: 61b7aaac3b55
Revises: 6b483af4b2db
Create Date: 2026-02-21 18:42:41.868718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61b7aaac3b55'
down_revision: Union[str, Sequence[str], None] = '6b483af4b2db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_subscriptions", sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_subscriptions", sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_subscriptions", sa.Column("provider", sa.String(length=20), nullable=False, server_default="stripe"))
    op.add_column("user_subscriptions", sa.Column("provider_customer_id", sa.String(length=120), nullable=True))
    op.add_column("user_subscriptions", sa.Column("provider_subscription_id", sa.String(length=120), nullable=True))
    op.add_column("user_subscriptions", sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_subscriptions", sa.Column("meta_json", sa.JSON(), nullable=True))
    op.add_column("user_subscriptions", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE user_subscriptions SET current_period_start = start_at WHERE current_period_start IS NULL")
    op.execute("UPDATE user_subscriptions SET current_period_end = end_at WHERE current_period_end IS NULL")
    op.execute("UPDATE user_subscriptions SET status='trial' WHERE status='active'")
    op.execute("UPDATE user_subscriptions SET updated_at = created_at WHERE updated_at IS NULL")

    op.alter_column("user_subscriptions", "current_period_start", nullable=False)
    op.alter_column("user_subscriptions", "current_period_end", nullable=False)

    op.drop_index("ix_user_subscriptions_status", table_name="user_subscriptions")
    op.drop_index("ix_user_subscriptions_user_id", table_name="user_subscriptions")

    op.drop_column("user_subscriptions", "auto_renew")
    op.drop_column("user_subscriptions", "start_at")
    op.drop_column("user_subscriptions", "end_at")

    op.create_index("ix_user_subscriptions_user", "user_subscriptions", ["user_id"], unique=True)
    op.create_index("ix_user_subscriptions_status", "user_subscriptions", ["status"])

    op.drop_constraint("user_subscriptions_plan_id_fkey", "user_subscriptions", type_="foreignkey")
    op.create_foreign_key("fk_user_subscriptions_plan", "user_subscriptions", "plans", ["plan_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_user_subscriptions_plan", "user_subscriptions", type_="foreignkey")
    op.create_foreign_key("user_subscriptions_plan_id_fkey", "user_subscriptions", "subscription_plans", ["plan_id"], ["id"])

    op.drop_index("ix_user_subscriptions_status", table_name="user_subscriptions")
    op.drop_index("ix_user_subscriptions_user", table_name="user_subscriptions")

    op.add_column("user_subscriptions", sa.Column("auto_renew", sa.Boolean(), nullable=True))
    op.add_column("user_subscriptions", sa.Column("start_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("user_subscriptions", sa.Column("end_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE user_subscriptions SET start_at = current_period_start WHERE start_at IS NULL")
    op.execute("UPDATE user_subscriptions SET end_at = current_period_end WHERE end_at IS NULL")

    op.drop_column("user_subscriptions", "updated_at")
    op.drop_column("user_subscriptions", "meta_json")
    op.drop_column("user_subscriptions", "canceled_at")
    op.drop_column("user_subscriptions", "provider_subscription_id")
    op.drop_column("user_subscriptions", "provider_customer_id")
    op.drop_column("user_subscriptions", "provider")
    op.drop_column("user_subscriptions", "current_period_end")
    op.drop_column("user_subscriptions", "current_period_start")

    op.create_index("ix_user_subscriptions_user_id", "user_subscriptions", ["user_id"], unique=True)
    op.create_index("ix_user_subscriptions_status", "user_subscriptions", ["status"])
