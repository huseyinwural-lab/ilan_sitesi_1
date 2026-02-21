"""
P31: listing contact options
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'p31_listing_contact_options'
down_revision: Union[str, Sequence[str], None] = 'p30_user_quota_limits'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('listings', sa.Column('contact_option_phone', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('listings', sa.Column('contact_option_message', sa.Boolean(), nullable=False, server_default=sa.text('true')))


def downgrade() -> None:
    op.drop_column('listings', 'contact_option_message')
    op.drop_column('listings', 'contact_option_phone')
