"""user_subscriptions v1

Revision ID: 61b7aaac3b55
Revises: 6b483af4b2db
Create Date: 2026-02-21 18:42:41.868718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61b7aaac3b55'
down_revision: Union[str, Sequence[str], None] = '6b483af4b2db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
