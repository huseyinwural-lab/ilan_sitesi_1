"""Vehicle Master Data

Revision ID: 4b5418a88ea6
Revises: 4b5418a88ea5
Create Date: 2026-02-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4b5418a88ea6'
down_revision = '4b5418a88ea5'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create Makes Table
    op.create_table(
        'vehicle_makes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('vehicle_types', postgresql.ARRAY(sa.String), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('source_ref', sa.String(100), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_vehicle_makes_slug', 'vehicle_makes', ['slug'], unique=True)

    # 2. Create Models Table
    op.create_table(
        'vehicle_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_makes.id'), nullable=False),
        sa.Column('slug', sa.String(100), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('vehicle_type', sa.String(20), nullable=False),
        sa.Column('year_from', sa.Integer(), nullable=True),
        sa.Column('year_to', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_vehicle_models_slug', 'vehicle_models', ['slug'])
    op.create_index('ix_vehicle_models_make_id', 'vehicle_models', ['make_id'])
    op.create_unique_constraint('uq_make_model', 'vehicle_models', ['make_id', 'slug'])

    # 3. Update Listings Table (Use reflection or check existence first if rerunning)
    # Alembic handles idempotent adds if we check properly, but op.add_column fails if exists.
    # We assume clean slate or forward migration.
    
    # Check if column exists first (Safety for re-run)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c['name'] for c in insp.get_columns('listings')]
    
    if 'make_id' not in columns:
        op.add_column('listings', sa.Column('make_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_makes.id'), nullable=True))
        op.create_index('ix_listings_make_id', 'listings', ['make_id'])
        
    if 'model_id' not in columns:
        op.add_column('listings', sa.Column('model_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('vehicle_models.id'), nullable=True))
        op.create_index('ix_listings_model_id', 'listings', ['model_id'])

def downgrade() -> None:
    op.drop_index('ix_listings_model_id', table_name='listings')
    op.drop_index('ix_listings_make_id', table_name='listings')
    op.drop_column('listings', 'model_id')
    op.drop_column('listings', 'make_id')
    op.drop_table('vehicle_models')
    op.drop_table('vehicle_makes')
