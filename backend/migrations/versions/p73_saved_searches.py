"""add saved searches table

Revision ID: p73_saved_searches
Revises: p72_listing_design_configs
Create Date: 2026-03-02 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p73_saved_searches"
down_revision: Union[str, Sequence[str], None] = "p72_listing_design_configs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS saved_searches (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            name VARCHAR(120) NOT NULL,
            filters_json JSON NOT NULL DEFAULT '{}'::json,
            query_string TEXT NOT NULL DEFAULT '',
            email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
            push_enabled BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_saved_searches_user_id ON saved_searches (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_saved_searches_user_created ON saved_searches (user_id, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_saved_searches_user_created")
    op.execute("DROP INDEX IF EXISTS ix_saved_searches_user_id")
    op.execute("DROP TABLE IF EXISTS saved_searches")
