"""Add tier to dealer_packages

Revision ID: 4b5418a88ea5
Revises: 4b5418a88ea4
Create Date: 2026-02-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '4b5418a88ea5'
down_revision = '4b5418a88ea4'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add column with default
    op.add_column('dealer_packages', sa.Column('tier', sa.String(length=20), server_default='STANDARD', nullable=False))
    
    # Create index
    op.create_index(op.f('ix_dealer_packages_tier'), 'dealer_packages', ['tier'], unique=False)
    
    # Backfill Data based on key
    # 'BASIC' -> 'STANDARD'
    # 'PRO' -> 'PREMIUM'
    # 'ENTERPRISE' -> 'ENTERPRISE'
    
    op.execute("UPDATE dealer_packages SET tier = 'STANDARD' WHERE key = 'BASIC'")
    op.execute("UPDATE dealer_packages SET tier = 'PREMIUM' WHERE key = 'PRO'")
    op.execute("UPDATE dealer_packages SET tier = 'ENTERPRISE' WHERE key = 'ENTERPRISE'")

def downgrade() -> None:
    op.drop_index(op.f('ix_dealer_packages_tier'), table_name='dealer_packages')
    op.drop_column('dealer_packages', 'tier')
