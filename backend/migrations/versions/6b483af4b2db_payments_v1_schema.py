"""payments v1 schema

Revision ID: 6b483af4b2db
Revises: d827659f4150
Create Date: 2026-02-21 18:26:10.228327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b483af4b2db'
down_revision: Union[str, Sequence[str], None] = 'd827659f4150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id UUID PRIMARY KEY,
            provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
            provider_payment_id VARCHAR(120),
            invoice_id UUID NOT NULL,
            dealer_id UUID,
            amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            currency VARCHAR(5) NOT NULL DEFAULT 'EUR',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            paid_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS payment_transactions (
            id UUID PRIMARY KEY,
            provider VARCHAR(20) NOT NULL DEFAULT 'stripe',
            session_id VARCHAR(120) NOT NULL UNIQUE,
            provider_payment_id VARCHAR(120),
            invoice_id UUID NOT NULL,
            dealer_id UUID NOT NULL,
            amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
            currency VARCHAR(5) NOT NULL DEFAULT 'EUR',
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid',
            metadata_json JSON,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )

    op.add_column("payments", sa.Column("provider_ref", sa.String(length=120), nullable=True))
    op.add_column("payments", sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("payments", sa.Column("amount_total", sa.Numeric(12, 2), nullable=True))
    op.add_column("payments", sa.Column("meta_json", sa.JSON(), nullable=True))

    op.alter_column("payments", "status", existing_type=sa.String(length=20), type_=sa.String(length=40))
    op.alter_column("payment_transactions", "status", existing_type=sa.String(length=20), type_=sa.String(length=40))
    op.alter_column("payment_transactions", "payment_status", existing_type=sa.String(length=20), type_=sa.String(length=40))

    op.execute("UPDATE payments SET provider_ref = provider_payment_id WHERE provider_ref IS NULL")
    op.execute("UPDATE payments SET user_id = dealer_id WHERE user_id IS NULL")
    op.execute("UPDATE payments SET amount_total = amount WHERE amount_total IS NULL")
    op.execute("UPDATE payments SET status='requires_payment_method' WHERE status='pending'")

    op.alter_column("payments", "provider_ref", nullable=False)
    op.alter_column("payments", "user_id", nullable=False)
    op.alter_column("payments", "amount_total", nullable=False)

    op.execute("ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_provider_payment_id_key")

    op.execute("DROP INDEX IF EXISTS ix_payments_dealer")
    op.execute("DROP INDEX IF EXISTS ix_payments_status")
    op.execute("DROP INDEX IF EXISTS ix_payments_invoice")

    op.drop_column("payments", "provider_payment_id")
    op.drop_column("payments", "dealer_id")
    op.drop_column("payments", "amount")
    op.drop_column("payments", "paid_at")

    op.create_unique_constraint("uq_payments_provider_ref", "payments", ["provider", "provider_ref"])
    op.create_index("ix_payments_invoice", "payments", ["invoice_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_index("ix_payments_created", "payments", ["created_at"])

    op.create_foreign_key("fk_payments_invoice", "payments", "admin_invoices", ["invoice_id"], ["id"])
    op.create_foreign_key("fk_payments_user", "payments", "users", ["user_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_payments_user", "payments", type_="foreignkey")
    op.drop_constraint("fk_payments_invoice", "payments", type_="foreignkey")

    op.drop_index("ix_payments_created", table_name="payments")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_invoice", table_name="payments")
    op.drop_constraint("uq_payments_provider_ref", "payments", type_="unique")

    op.alter_column("payment_transactions", "payment_status", existing_type=sa.String(length=40), type_=sa.String(length=20))
    op.alter_column("payment_transactions", "status", existing_type=sa.String(length=40), type_=sa.String(length=20))
    op.alter_column("payments", "status", existing_type=sa.String(length=40), type_=sa.String(length=20))

    op.add_column("payments", sa.Column("provider_payment_id", sa.String(length=120), nullable=True))
    op.add_column("payments", sa.Column("dealer_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("payments", sa.Column("amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("payments", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))

    op.execute("UPDATE payments SET provider_payment_id = provider_ref WHERE provider_payment_id IS NULL")
    op.execute("UPDATE payments SET dealer_id = user_id WHERE dealer_id IS NULL")
    op.execute("UPDATE payments SET amount = amount_total WHERE amount IS NULL")

    op.alter_column("payments", "provider_payment_id", nullable=True)
    op.alter_column("payments", "dealer_id", nullable=True)
    op.alter_column("payments", "amount", nullable=True)

    op.add_column("payments", sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"))

    op.create_index("ix_payments_invoice", "payments", ["invoice_id"])
    op.create_index("ix_payments_dealer", "payments", ["dealer_id"])
    op.create_index("ix_payments_status", "payments", ["status"])

    op.create_unique_constraint("payments_provider_payment_id_key", "payments", ["provider_payment_id"])

    op.drop_column("payments", "meta_json")
    op.drop_column("payments", "amount_total")
    op.drop_column("payments", "user_id")
    op.drop_column("payments", "provider_ref")
