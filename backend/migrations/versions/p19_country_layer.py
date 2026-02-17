
"""
P19: Country Abstraction Layer Update
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p19_country_layer'
down_revision: Union[str, Sequence[str], None] = 'f83f2eddec93'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Update listings table (Ensure country column is robust)
    # Listings already has 'country' column (String 5). We will add index.
    # Check if index exists first? Alembic creates if not.
    op.create_index(op.f('ix_listings_country_city_category'), 'listings', ['country', 'city', 'category_id'], unique=False)

    # 2. Update users table
    # Users table needs country_code column if not exists.
    # Current User model has 'country_scope' JSON list.
    # We need a primary 'country_code' for the user's main location/billing entity.
    op.add_column('users', sa.Column('country_code', sa.String(length=5), server_default='TR', nullable=False))
    op.create_index(op.f('ix_users_country_code'), 'users', ['country_code'], unique=False)

    # 3. Update subscription_plans table
    # Plans need to be country specific
    op.add_column('subscription_plans', sa.Column('country_code', sa.String(length=5), server_default='TR', nullable=False))
    op.create_index(op.f('ix_subscription_plans_country'), 'subscription_plans', ['country_code'], unique=False)
    
    # 4. Update growth_events
    op.add_column('growth_events', sa.Column('country_code', sa.String(length=5), nullable=True))
    op.create_index(op.f('ix_growth_events_country'), 'growth_events', ['country_code'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_growth_events_country'), table_name='growth_events')
    op.drop_column('growth_events', 'country_code')
    
    op.drop_index(op.f('ix_subscription_plans_country'), table_name='subscription_plans')
    op.drop_column('subscription_plans', 'country_code')
    
    op.drop_index(op.f('ix_users_country_code'), table_name='users')
    op.drop_column('users', 'country_code')
    
    op.drop_index(op.f('ix_listings_country_city_category'), table_name='listings')
