"""
P50: Pricing campaign items
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p50_pricing_campaign_items"
down_revision: Union[str, Sequence[str], None] = "p49_pricing_tiers_packages"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_campaign_items" not in tables:
        op.create_table(
            "pricing_campaign_items",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("scope", sa.String(length=20), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=True),
            sa.Column("listing_quota", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("price_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
            sa.Column("publish_days", sa.Integer(), nullable=False, server_default="90"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "pricing_campaign_items" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaign_items")}
        if "ix_pricing_campaign_items_scope_active" not in indexes:
            op.create_index("ix_pricing_campaign_items_scope_active", "pricing_campaign_items", ["scope", "is_active"])
        if "ix_pricing_campaign_items_scope_deleted" not in indexes:
            op.create_index("ix_pricing_campaign_items_scope_deleted", "pricing_campaign_items", ["scope", "is_deleted"])
        if "ix_pricing_campaign_items_end_at" not in indexes:
            op.create_index("ix_pricing_campaign_items_end_at", "pricing_campaign_items", ["end_at"])
        if "uq_pricing_campaign_items_active_scope" not in indexes:
            op.create_index(
                "uq_pricing_campaign_items_active_scope",
                "pricing_campaign_items",
                ["scope"],
                unique=True,
                postgresql_where=sa.text("is_active = true AND is_deleted = false"),
            )

    if "pricing_price_snapshots" in tables:
        columns = {col["name"] for col in inspector.get_columns("pricing_price_snapshots")}
        if "campaign_item_id" not in columns:
            op.add_column(
                "pricing_price_snapshots",
                sa.Column("campaign_item_id", postgresql.UUID(as_uuid=True), nullable=True),
            )
            op.create_foreign_key(
                "fk_pricing_snapshot_campaign_item",
                "pricing_price_snapshots",
                "pricing_campaign_items",
                ["campaign_item_id"],
                ["id"],
            )
        if "listing_quota" not in columns:
            op.add_column("pricing_price_snapshots", sa.Column("listing_quota", sa.Integer(), nullable=True))
        if "publish_days" not in columns:
            op.add_column("pricing_price_snapshots", sa.Column("publish_days", sa.Integer(), nullable=True))
        if "campaign_override_active" not in columns:
            op.add_column(
                "pricing_price_snapshots",
                sa.Column("campaign_override_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_price_snapshots" in tables:
        columns = {col["name"] for col in inspector.get_columns("pricing_price_snapshots")}
        fks = {fk.get("name") for fk in inspector.get_foreign_keys("pricing_price_snapshots")}
        if "fk_pricing_snapshot_campaign_item" in fks:
            op.drop_constraint("fk_pricing_snapshot_campaign_item", "pricing_price_snapshots", type_="foreignkey")
        if "campaign_override_active" in columns:
            op.drop_column("pricing_price_snapshots", "campaign_override_active")
        if "publish_days" in columns:
            op.drop_column("pricing_price_snapshots", "publish_days")
        if "listing_quota" in columns:
            op.drop_column("pricing_price_snapshots", "listing_quota")
        if "campaign_item_id" in columns:
            op.drop_column("pricing_price_snapshots", "campaign_item_id")

    if "pricing_campaign_items" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaign_items")}
        if "uq_pricing_campaign_items_active_scope" in indexes:
            op.drop_index("uq_pricing_campaign_items_active_scope", table_name="pricing_campaign_items")
        if "ix_pricing_campaign_items_end_at" in indexes:
            op.drop_index("ix_pricing_campaign_items_end_at", table_name="pricing_campaign_items")
        if "ix_pricing_campaign_items_scope_deleted" in indexes:
            op.drop_index("ix_pricing_campaign_items_scope_deleted", table_name="pricing_campaign_items")
        if "ix_pricing_campaign_items_scope_active" in indexes:
            op.drop_index("ix_pricing_campaign_items_scope_active", table_name="pricing_campaign_items")
        op.drop_table("pricing_campaign_items")
