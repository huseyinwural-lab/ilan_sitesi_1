"""Shopping Attribute v2

Revision ID: 4b5418a88ea7
Revises: 4b5418a88ea6
Create Date: 2026-03-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4b5418a88ea7'
down_revision = '4b5418a88ea6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. Create Listing Attributes Table (EAV Typed)
    op.create_table(
        'listing_attributes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('listing_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('listings.id', ondelete="CASCADE"), nullable=False),
        sa.Column('attribute_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attributes.id'), nullable=False),
        
        # Typed Values
        sa.Column('value_text', sa.String(255), nullable=True),
        sa.Column('value_number', sa.Numeric(12, 2), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_option_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attribute_options.id'), nullable=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Indexes for Performance
    op.create_index('ix_listing_attributes_listing_id', 'listing_attributes', ['listing_id'])
    op.create_index('ix_listing_attributes_attr_val_opt', 'listing_attributes', ['attribute_id', 'value_option_id'])
    op.create_index('ix_listing_attributes_attr_val_num', 'listing_attributes', ['attribute_id', 'value_number'])

    # 2. Add is_variant to Attributes Table
    # Check if exists first (Idempotency)
    conn = op.get_bind()
    insp = sa.inspect(conn)
    columns = [c['name'] for c in insp.get_columns('attributes')]
    if 'is_variant' not in columns:
        op.add_column('attributes', sa.Column('is_variant', sa.Boolean(), server_default='false'))

def downgrade() -> None:
    op.drop_column('attributes', 'is_variant')
    op.drop_table('listing_attributes')
