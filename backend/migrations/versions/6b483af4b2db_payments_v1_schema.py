"""payments v1 schema

Revision ID: 6b483af4b2db
Revises: d827659f4150
Create Date: 2026-02-21 18:26:10.228327

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6b483af4b2db'
down_revision: Union[str, Sequence[str], None] = 'd827659f4150'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
