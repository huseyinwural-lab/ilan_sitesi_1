
"""Add premium fields to listings

Revision ID: p17_premium_fields
Revises: 717de866a1ac
Create Date: 2026-02-16 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'p17_premium_fields'
down_revision: Union[str, Sequence[str], None] = '717de866a1ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new premium fields
    op.add_column('listings', sa.Column('boosted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('listings', sa.Column('is_urgent', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('listings', sa.Column('urgent_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('listings', sa.Column('is_bold_title', sa.Boolean(), server_default='false', nullable=False))
    
    # Add indexes for performance
    op.create_index(op.f('ix_listings_boosted_at'), 'listings', ['boosted_at'], unique=False)
    op.create_index(op.f('ix_listings_is_urgent'), 'listings', ['is_urgent'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_listings_is_urgent'), table_name='listings')
    op.drop_index(op.f('ix_listings_boosted_at'), table_name='listings')
    op.drop_column('listings', 'is_bold_title')
    op.drop_column('listings', 'urgent_expires_at')
    op.drop_column('listings', 'is_urgent')
    op.drop_column('listings', 'boosted_at')
