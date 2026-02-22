"""
P35: add price_type and hourly_rate to listings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'p35_listing_price_type_hourly_rate'
down_revision: Union[str, Sequence[str], None] = 'p34_dealer_gdpr_deleted_at'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'listings' not in inspector.get_table_names():
        return
    columns = [column['name'] for column in inspector.get_columns('listings')]

    if 'price_type' not in columns:
        price_enum = sa.Enum('FIXED', 'HOURLY', name='price_type_enum')
        price_enum.create(conn, checkfirst=True)
        op.add_column('listings', sa.Column('price_type', price_enum, nullable=False, server_default='FIXED'))

    if 'hourly_rate' not in columns:
        op.add_column('listings', sa.Column('hourly_rate', sa.Float(), nullable=True))

    constraints = [c['name'] for c in inspector.get_check_constraints('listings')]
    if 'ck_listings_price_single_mode' not in constraints:
        op.create_check_constraint(
            'ck_listings_price_single_mode',
            'listings',
            'NOT (price IS NOT NULL AND hourly_rate IS NOT NULL)'
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'listings' not in inspector.get_table_names():
        return
    columns = [column['name'] for column in inspector.get_columns('listings')]
    constraints = [c['name'] for c in inspector.get_check_constraints('listings')]

    if 'ck_listings_price_single_mode' in constraints:
        op.drop_constraint('ck_listings_price_single_mode', 'listings', type_='check')

    if 'hourly_rate' in columns:
        op.drop_column('listings', 'hourly_rate')

    if 'price_type' in columns:
        op.drop_column('listings', 'price_type')
        op.execute('DROP TYPE IF EXISTS price_type_enum')
