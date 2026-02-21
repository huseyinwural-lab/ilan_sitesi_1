"""
P30: add user quota limits
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p30_user_quota_limits'
down_revision: Union[str, Sequence[str], None] = 'p29_email_verification_tokens'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('listing_quota_limit', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('showcase_quota_limit', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'showcase_quota_limit')
    op.drop_column('users', 'listing_quota_limit')
