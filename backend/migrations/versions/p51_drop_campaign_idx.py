"""
P51: Drop unique index for pricing campaign items
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p51_drop_campaign_idx"
down_revision: Union[str, Sequence[str], None] = "p50_pricing_campaign_items"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "pricing_campaign_items" not in inspector.get_table_names():
        return
    indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaign_items")}
    if "uq_pricing_campaign_items_active_scope" in indexes:
        op.drop_index("uq_pricing_campaign_items_active_scope", table_name="pricing_campaign_items")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "pricing_campaign_items" not in inspector.get_table_names():
        return
    indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaign_items")}
    if "uq_pricing_campaign_items_active_scope" not in indexes:
        op.create_index(
            "uq_pricing_campaign_items_active_scope",
            "pricing_campaign_items",
            ["scope"],
            unique=True,
            postgresql_where=sa.text("is_active = true AND is_deleted = false"),
        )
