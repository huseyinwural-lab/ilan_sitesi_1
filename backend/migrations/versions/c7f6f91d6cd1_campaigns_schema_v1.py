"""campaigns schema v1

Revision ID: c7f6f91d6cd1
Revises: 5710cb21ddfd
Create Date: 2026-02-21 17:17:02.725955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f6f91d6cd1'
down_revision: Union[str, Sequence[str], None] = '5710cb21ddfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
