"""
P36: create listings_search table + indexes for public search
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p36_listings_search_index'
down_revision: Union[str, Sequence[str], None] = 'p35_price_type_hourly'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'listings_search' in inspector.get_table_names():
        return

    op.create_table(
        'listings_search',
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('module', sa.String(length=50), nullable=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('country_code', sa.String(length=5), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('price_amount', sa.Numeric(12, 2), nullable=True),
        sa.Column('price_type', sa.String(length=20), nullable=True),
        sa.Column('hourly_rate', sa.Numeric(12, 2), nullable=True),
        sa.Column('currency', sa.String(length=5), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_showcase', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('seller_type', sa.String(length=20), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('model_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('attributes', postgresql.JSONB(), nullable=True),
        sa.Column('images', postgresql.JSONB(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.Column(
            'tsv_tr',
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('turkish', coalesce(title, '') || ' ' || coalesce(description, ''))", persisted=True),
            nullable=True,
        ),
        sa.Column(
            'tsv_de',
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('german', coalesce(title, '') || ' ' || coalesce(description, ''))", persisted=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(['listing_id'], ['listings.id'], ondelete='CASCADE'),
    )

    op.create_index('ix_listings_search_tsv_tr', 'listings_search', ['tsv_tr'], postgresql_using='gin')
    op.create_index('ix_listings_search_tsv_de', 'listings_search', ['tsv_de'], postgresql_using='gin')
    op.create_index('ix_listings_search_core', 'listings_search', ['status', 'country_code', 'module', 'published_at'])
    op.create_index('ix_listings_search_category_price', 'listings_search', ['category_id', 'price_amount'])
    op.create_index('ix_listings_search_make_model_year', 'listings_search', ['make_id', 'model_id', 'year'])
    op.create_index('ix_listings_search_seller', 'listings_search', ['seller_type', 'is_verified', 'published_at'])
    op.create_index('ix_listings_search_attrs_gin', 'listings_search', ['attributes'], postgresql_using='gin')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'listings_search' not in inspector.get_table_names():
        return

    op.drop_index('ix_listings_search_attrs_gin', table_name='listings_search')
    op.drop_index('ix_listings_search_seller', table_name='listings_search')
    op.drop_index('ix_listings_search_make_model_year', table_name='listings_search')
    op.drop_index('ix_listings_search_category_price', table_name='listings_search')
    op.drop_index('ix_listings_search_core', table_name='listings_search')
    op.drop_index('ix_listings_search_tsv_de', table_name='listings_search')
    op.drop_index('ix_listings_search_tsv_tr', table_name='listings_search')
    op.drop_table('listings_search')
