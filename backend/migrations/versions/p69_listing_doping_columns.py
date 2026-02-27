"""add listing doping timestamps

Revision ID: p69_listing_doping_cols
Revises: p68_ops_alert_delivery_idx
Create Date: 2026-02-27 18:52:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p69_listing_doping_cols"
down_revision: Union[str, Sequence[str], None] = "p68_ops_alert_delivery_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE listings ADD COLUMN IF NOT EXISTS featured_until TIMESTAMPTZ")
    op.execute("ALTER TABLE listings ADD COLUMN IF NOT EXISTS urgent_until TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_featured_until ON listings (featured_until)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_urgent_until ON listings (urgent_until)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_listings_featured_until")
    op.execute("DROP INDEX IF EXISTS ix_listings_urgent_until")
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS featured_until")
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS urgent_until")
