"""add paid listing field and campaign listing_type

Revision ID: p70_paid_listing_campaign_type
Revises: p69_listing_doping_cols
Create Date: 2026-02-27 20:16:00.000000
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p70_paid_listing_campaign_type"
down_revision: Union[str, Sequence[str], None] = "p69_listing_doping_cols"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE listings ADD COLUMN IF NOT EXISTS paid_until TIMESTAMPTZ")
    op.execute("CREATE INDEX IF NOT EXISTS ix_listings_paid_until ON listings (paid_until)")

    op.execute("ALTER TABLE pricing_campaign_items ADD COLUMN IF NOT EXISTS listing_type VARCHAR(20)")
    op.execute("UPDATE pricing_campaign_items SET listing_type = 'free' WHERE listing_type IS NULL OR listing_type = ''")
    op.execute("ALTER TABLE pricing_campaign_items ALTER COLUMN listing_type SET DEFAULT 'free'")
    op.execute("CREATE INDEX IF NOT EXISTS ix_pricing_campaign_items_scope_type_active ON pricing_campaign_items (scope, listing_type, is_active)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_pricing_campaign_items_scope_type_active")
    op.execute("ALTER TABLE pricing_campaign_items DROP COLUMN IF EXISTS listing_type")

    op.execute("DROP INDEX IF EXISTS ix_listings_paid_until")
    op.execute("ALTER TABLE listings DROP COLUMN IF EXISTS paid_until")
