"""add listing design configs table

Revision ID: p72_listing_design_configs
Revises: p71_site_showcase_layouts
Create Date: 2026-03-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p72_listing_design_configs"
down_revision: Union[str, Sequence[str], None] = "p71_site_showcase_layouts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS listing_design_configs (
            id UUID PRIMARY KEY,
            payload JSON NOT NULL,
            status VARCHAR(16) NOT NULL DEFAULT 'draft',
            version INTEGER NOT NULL DEFAULT 1,
            published_at TIMESTAMPTZ NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_listing_design_configs_status ON listing_design_configs (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listing_design_configs_version ON listing_design_configs (version)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_listing_design_configs_version")
    op.execute("DROP INDEX IF EXISTS ix_listing_design_configs_status")
    op.execute("DROP TABLE IF EXISTS listing_design_configs")
