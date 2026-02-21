"""add notifications table v1

Revision ID: 5710cb21ddfd
Revises: p28_email_verification_fields
Create Date: 2026-02-21 16:26:10.211664

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5710cb21ddfd'
down_revision: Union[str, Sequence[str], None] = 'p28_email_verification_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
