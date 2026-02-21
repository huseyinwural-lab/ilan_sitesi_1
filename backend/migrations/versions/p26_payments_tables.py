"""P26: Payments tables and invoice payment status
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p26_payments_tables'
down_revision: Union[str, Sequence[str], None] = 'p25_admin_invoices_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('admin_invoices', sa.Column('payment_status', sa.String(length=40), nullable=False, server_default='requires_payment_method'))

    op.create_table(
        'payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dealer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='stripe'),
        sa.Column('provider_payment_id', sa.String(length=120), nullable=True, unique=True),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=5), nullable=False, server_default='EUR'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_payments_invoice', 'payments', ['invoice_id'])
    op.create_index('ix_payments_dealer', 'payments', ['dealer_id'])
    op.create_index('ix_payments_status', 'payments', ['status'])

    op.create_table(
        'payment_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='stripe'),
        sa.Column('session_id', sa.String(length=120), nullable=False, unique=True),
        sa.Column('provider_payment_id', sa.String(length=120), nullable=True),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('dealer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency', sa.String(length=5), nullable=False, server_default='EUR'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='unpaid'),
        sa.Column('metadata_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_payment_transactions_invoice', 'payment_transactions', ['invoice_id'])
    op.create_index('ix_payment_transactions_dealer', 'payment_transactions', ['dealer_id'])
    op.create_index('ix_payment_transactions_status', 'payment_transactions', ['status'])

    op.create_table(
        'payment_event_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('provider', sa.String(length=20), nullable=False, server_default='stripe'),
        sa.Column('event_id', sa.String(length=120), nullable=False, unique=True),
        sa.Column('event_type', sa.String(length=120), nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_payment_event_logs_type', 'payment_event_logs', ['event_type'])


def downgrade() -> None:
    op.drop_index('ix_payment_event_logs_type', table_name='payment_event_logs')
    op.drop_table('payment_event_logs')

    op.drop_index('ix_payment_transactions_status', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_dealer', table_name='payment_transactions')
    op.drop_index('ix_payment_transactions_invoice', table_name='payment_transactions')
    op.drop_table('payment_transactions')

    op.drop_index('ix_payments_status', table_name='payments')
    op.drop_index('ix_payments_dealer', table_name='payments')
    op.drop_index('ix_payments_invoice', table_name='payments')
    op.drop_table('payments')

    op.drop_column('admin_invoices', 'payment_status')
