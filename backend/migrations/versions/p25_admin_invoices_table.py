"""
P25: Admin invoices table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p25_admin_invoices_table'
down_revision: Union[str, Sequence[str], None] = 'p24_plans_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'admin_invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('invoice_no', sa.String(length=50), nullable=False, unique=True),
        sa.Column('dealer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency_code', sa.String(length=5), nullable=False, server_default='EUR'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scope', sa.String(length=20), nullable=False, server_default='country'),
        sa.Column('country_code', sa.String(length=10), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    op.create_index('ix_admin_invoices_dealer', 'admin_invoices', ['dealer_id'])
    op.create_index('ix_admin_invoices_status', 'admin_invoices', ['status'])
    op.create_index('ix_admin_invoices_country', 'admin_invoices', ['country_code'])


def downgrade() -> None:
    op.drop_index('ix_admin_invoices_country', table_name='admin_invoices')
    op.drop_index('ix_admin_invoices_status', table_name='admin_invoices')
    op.drop_index('ix_admin_invoices_dealer', table_name='admin_invoices')
    op.drop_table('admin_invoices')
