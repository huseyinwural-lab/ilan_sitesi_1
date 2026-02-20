"""
P24: Plans table (admin plans)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'p24_plans_table'
down_revision: Union[str, Sequence[str], None] = 'p23_vehicle_type_dimension'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'plans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('slug', sa.String(length=120), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('country_scope', sa.String(length=20), nullable=False, server_default='global'),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('price_amount', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('currency_code', sa.String(length=5), nullable=False, server_default='EUR'),
        sa.Column('listing_quota', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('showcase_quota', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('active_flag', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('country_scope', 'country_code', 'slug', name='uq_plans_scope_country_slug'),
    )
    op.create_index('ix_plans_country_scope', 'plans', ['country_scope'])
    op.create_index('ix_plans_country_code', 'plans', ['country_code'])
    op.create_index('ix_plans_active_flag', 'plans', ['active_flag'])
    op.create_index('ix_plans_archived_at', 'plans', ['archived_at'])


def downgrade() -> None:
    op.drop_index('ix_plans_archived_at', table_name='plans')
    op.drop_index('ix_plans_active_flag', table_name='plans')
    op.drop_index('ix_plans_country_code', table_name='plans')
    op.drop_index('ix_plans_country_scope', table_name='plans')
    op.drop_table('plans')
