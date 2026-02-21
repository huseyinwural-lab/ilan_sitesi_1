"""invoices v1 schema

Revision ID: d827659f4150
Revises: 6a51163ba322
Create Date: 2026-02-21 18:08:20.694824

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd827659f4150'
down_revision: Union[str, Sequence[str], None] = '6a51163ba322'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
