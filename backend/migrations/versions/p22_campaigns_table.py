"""
P22: Campaigns table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p22_campaigns_table'
down_revision: Union[str, Sequence[str], None] = 'p21_auth_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('country_scope', sa.String(length=20), nullable=False, server_default='global'),
        sa.Column('country_code', sa.String(length=5), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='medium'),
        sa.Column('duration_days', sa.Integer(), nullable=True),
        sa.Column('quota_count', sa.Integer(), nullable=True),
        sa.Column('price_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency_code', sa.String(length=5), nullable=True),
        sa.Column('created_by_admin_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_admin_id'], ['users.id']),
    )

    op.create_index('ix_campaigns_type', 'campaigns', ['type'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    op.create_index('ix_campaigns_start_at', 'campaigns', ['start_at'])
    op.create_index('ix_campaigns_end_at', 'campaigns', ['end_at'])
    op.create_index('ix_campaigns_country_code', 'campaigns', ['country_code'])
    op.create_index('ix_campaigns_priority', 'campaigns', ['priority'])


def downgrade() -> None:
    op.drop_index('ix_campaigns_priority', table_name='campaigns')
    op.drop_index('ix_campaigns_country_code', table_name='campaigns')
    op.drop_index('ix_campaigns_end_at', table_name='campaigns')
    op.drop_index('ix_campaigns_start_at', table_name='campaigns')
    op.drop_index('ix_campaigns_status', table_name='campaigns')
    op.drop_index('ix_campaigns_type', table_name='campaigns')
    op.drop_table('campaigns')
