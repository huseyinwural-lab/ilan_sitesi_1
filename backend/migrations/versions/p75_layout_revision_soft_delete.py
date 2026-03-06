"""add is_deleted to layout_revisions

Revision ID: p75_layout_revision_soft_delete
Revises: p74_layout_builder_foundation
Create Date: 2026-03-06 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p75_layout_revision_soft_delete"
down_revision: Union[str, Sequence[str], None] = "p74_layout_builder_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE layout_revisions
        ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_revisions_is_deleted
        ON layout_revisions (is_deleted)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_layout_revisions_is_deleted")
    op.execute(
        """
        ALTER TABLE layout_revisions
        DROP COLUMN IF EXISTS is_deleted
        """
    )
