"""webhook event log

Revision ID: c5833a1fffde
Revises: 61b7aaac3b55
Create Date: 2026-02-21 19:04:28.375277

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5833a1fffde'
down_revision: Union[str, Sequence[str], None] = '61b7aaac3b55'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
