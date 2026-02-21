"""
P27: Add slug to dealer_profiles
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p27_dealer_profile_slug'
down_revision: Union[str, Sequence[str], None] = 'p26_payments_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('dealer_profiles', sa.Column('slug', sa.String(length=120), nullable=True))
    op.create_index('ix_dealer_profiles_slug', 'dealer_profiles', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_dealer_profiles_slug', table_name='dealer_profiles')
    op.drop_column('dealer_profiles', 'slug')
