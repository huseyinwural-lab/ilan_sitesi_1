"""add site showcase layouts table

Revision ID: p71_site_showcase_layouts
Revises: p70_paid_listing_campaign_type
Create Date: 2026-02-27 21:28:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p71_site_showcase_layouts"
down_revision: Union[str, Sequence[str], None] = "p70_paid_listing_campaign_type"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS site_showcase_layouts (
            id UUID PRIMARY KEY,
            config JSON NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_site_showcase_layouts_status ON site_showcase_layouts (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_site_showcase_layouts_version ON site_showcase_layouts (version)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_site_showcase_layouts_version")
    op.execute("DROP INDEX IF EXISTS ix_site_showcase_layouts_status")
    op.execute("DROP TABLE IF EXISTS site_showcase_layouts")
