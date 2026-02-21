"""plans add period

Revision ID: 6a51163ba322
Revises: c7f6f91d6cd1
Create Date: 2026-02-21 17:17:56.801503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a51163ba322'
down_revision: Union[str, Sequence[str], None] = 'c7f6f91d6cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
