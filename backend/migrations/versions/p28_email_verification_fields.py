"""
P28: Email verification fields for users
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p28_email_verification_fields'
down_revision: Union[str, Sequence[str], None] = 'p27_dealer_profile_slug'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verification_code_hash', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('email_verification_expires_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('users', sa.Column('email_verification_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    op.drop_column('users', 'email_verification_attempts')
    op.drop_column('users', 'email_verification_expires_at')
    op.drop_column('users', 'email_verification_code_hash')
