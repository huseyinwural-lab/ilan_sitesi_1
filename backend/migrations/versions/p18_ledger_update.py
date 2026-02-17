
"""Make reward_id nullable in reward_ledger

Revision ID: p18_ledger_update
Revises: 0f8f8129feda
Create Date: 2026-02-16 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'p18_ledger_update'
down_revision: Union[str, Sequence[str], None] = '0f8f8129feda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make reward_id nullable
    op.alter_column('reward_ledger', 'reward_id',
               existing_type=sa.UUID(),
               nullable=True)
    
    # Add affiliate_id column
    op.add_column('reward_ledger', sa.Column('affiliate_id', sa.UUID(), nullable=True))
    op.create_foreign_key(None, 'reward_ledger', 'affiliates', ['affiliate_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint(None, 'reward_ledger', type_='foreignkey')
    op.drop_column('reward_ledger', 'affiliate_id')
    op.alter_column('reward_ledger', 'reward_id',
               existing_type=sa.UUID(),
               nullable=False)
