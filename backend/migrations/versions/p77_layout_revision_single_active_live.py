"""enforce single active live revision per layout page

Revision ID: p77_layout_revision_single_active_live
Revises: p76_layout_revision_active_state
Create Date: 2026-03-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p77_layout_revision_single_active_live"
down_revision: Union[str, Sequence[str], None] = "p76_layout_revision_active_state"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_revisions_single_active_live
        ON layout_revisions (layout_page_id)
        WHERE status = 'published' AND is_active = true AND is_deleted = false
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_layout_revisions_single_active_live")
