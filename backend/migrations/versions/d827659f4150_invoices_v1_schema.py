"""invoices v1 schema

Revision ID: d827659f4150
Revises: 6a51163ba322
Create Date: 2026-02-21 18:08:20.694824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd827659f4150'
down_revision: Union[str, Sequence[str], None] = '6a51163ba322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("admin_invoices", sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("admin_invoices", sa.Column("subscription_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("admin_invoices", sa.Column("campaign_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("admin_invoices", sa.Column("amount_total", sa.Numeric(12, 2), nullable=True))
    op.add_column("admin_invoices", sa.Column("currency", sa.String(length=5), nullable=True))
    op.add_column("admin_invoices", sa.Column("provider_customer_id", sa.String(length=120), nullable=True))
    op.add_column("admin_invoices", sa.Column("meta_json", sa.JSON(), nullable=True))

    op.alter_column("admin_invoices", "payment_status", existing_type=sa.String(length=20), type_=sa.String(length=40))

    op.alter_column("admin_invoices", "plan_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=True)
    op.alter_column("admin_invoices", "country_code", existing_type=sa.String(length=10), nullable=True)

    op.execute("UPDATE admin_invoices SET user_id = dealer_id WHERE user_id IS NULL")
    op.execute("UPDATE admin_invoices SET amount_total = amount WHERE amount_total IS NULL")
    op.execute("UPDATE admin_invoices SET currency = currency_code WHERE currency IS NULL")
    op.execute("UPDATE admin_invoices SET status='void' WHERE status='cancelled'")
    op.execute("UPDATE admin_invoices SET status='issued' WHERE status='overdue'")
    op.execute("UPDATE admin_invoices SET payment_status='requires_payment_method' WHERE payment_status='unpaid'")

    op.alter_column("admin_invoices", "user_id", nullable=False)
    op.alter_column("admin_invoices", "amount_total", nullable=False)
    op.alter_column("admin_invoices", "currency", nullable=False)

    op.drop_index("ix_admin_invoices_dealer", table_name="admin_invoices")
    op.drop_index("ix_admin_invoices_country", table_name="admin_invoices")
    op.drop_index("ix_admin_invoices_status", table_name="admin_invoices")

    op.drop_column("admin_invoices", "dealer_id")
    op.drop_column("admin_invoices", "amount")
    op.drop_column("admin_invoices", "currency_code")

    op.create_index("ix_admin_invoices_user", "admin_invoices", ["user_id"])
    op.create_index("ix_admin_invoices_status", "admin_invoices", ["status"])
    op.create_index("ix_admin_invoices_created", "admin_invoices", ["created_at"])

    op.create_foreign_key("fk_admin_invoices_user", "admin_invoices", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_admin_invoices_subscription", "admin_invoices", "user_subscriptions", ["subscription_id"], ["id"])
    op.create_foreign_key("fk_admin_invoices_plan", "admin_invoices", "plans", ["plan_id"], ["id"])
    op.create_foreign_key("fk_admin_invoices_campaign", "admin_invoices", "campaigns", ["campaign_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_admin_invoices_campaign", "admin_invoices", type_="foreignkey")
    op.drop_constraint("fk_admin_invoices_plan", "admin_invoices", type_="foreignkey")
    op.drop_constraint("fk_admin_invoices_subscription", "admin_invoices", type_="foreignkey")
    op.drop_constraint("fk_admin_invoices_user", "admin_invoices", type_="foreignkey")

    op.drop_index("ix_admin_invoices_created", table_name="admin_invoices")
    op.drop_index("ix_admin_invoices_status", table_name="admin_invoices")
    op.drop_index("ix_admin_invoices_user", table_name="admin_invoices")

    op.add_column("admin_invoices", sa.Column("dealer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("admin_invoices", sa.Column("amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("admin_invoices", sa.Column("currency_code", sa.String(length=5), nullable=True))

    op.execute("UPDATE admin_invoices SET dealer_id = user_id WHERE dealer_id IS NULL")
    op.execute("UPDATE admin_invoices SET amount = amount_total WHERE amount IS NULL")
    op.execute("UPDATE admin_invoices SET currency_code = currency WHERE currency_code IS NULL")

    op.alter_column("admin_invoices", "plan_id", existing_type=sa.dialects.postgresql.UUID(as_uuid=True), nullable=False)
    op.alter_column("admin_invoices", "country_code", existing_type=sa.String(length=10), nullable=False)

    op.drop_column("admin_invoices", "meta_json")
    op.drop_column("admin_invoices", "provider_customer_id")
    op.drop_column("admin_invoices", "currency")
    op.drop_column("admin_invoices", "amount_total")
    op.drop_column("admin_invoices", "campaign_id")
    op.drop_column("admin_invoices", "subscription_id")
    op.drop_column("admin_invoices", "user_id")

    op.create_index("ix_admin_invoices_dealer", "admin_invoices", ["dealer_id"])
    op.create_index("ix_admin_invoices_status", "admin_invoices", ["status"])
    op.create_index("ix_admin_invoices_country", "admin_invoices", ["country_code"])
