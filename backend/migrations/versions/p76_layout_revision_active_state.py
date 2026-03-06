"""add is_active to layout_revisions

Revision ID: p76_layout_revision_active_state
Revises: p75_layout_revision_soft_delete
Create Date: 2026-03-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p76_layout_revision_active_state"
down_revision: Union[str, Sequence[str], None] = "p75_layout_revision_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE layout_revisions
        ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_revisions_is_active
        ON layout_revisions (is_active)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_layout_revisions_is_active")
    op.execute(
        """
        ALTER TABLE layout_revisions
        DROP COLUMN IF EXISTS is_active
        """
    )
