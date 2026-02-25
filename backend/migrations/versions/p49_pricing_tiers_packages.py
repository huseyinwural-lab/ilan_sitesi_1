"""
P49: Pricing tiers, packages, subscriptions, snapshots
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p49_pricing_tiers_packages"
down_revision: Union[str, Sequence[str], None] = "p48_pricing_campaigns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_tier_rules" not in tables:
        op.create_table(
            "pricing_tier_rules",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("scope", sa.String(length=20), nullable=False, server_default="individual"),
            sa.Column("year_window", sa.String(length=20), nullable=False, server_default="calendar_year"),
            sa.Column("tier_no", sa.Integer(), nullable=False),
            sa.Column("listing_from", sa.Integer(), nullable=False),
            sa.Column("listing_to", sa.Integer(), nullable=True),
            sa.Column("price_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
            sa.Column("publish_days", sa.Integer(), nullable=False, server_default="90"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("effective_start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("effective_end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "pricing_packages" not in tables:
        op.create_table(
            "pricing_packages",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("scope", sa.String(length=20), nullable=False, server_default="corporate"),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("listing_quota", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("package_price_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
            sa.Column("publish_days", sa.Integer(), nullable=False, server_default="90"),
            sa.Column("package_duration_days", sa.Integer(), nullable=False, server_default="30"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "user_package_subscriptions" not in tables:
        op.create_table(
            "user_package_subscriptions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("package_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pricing_packages.id"), nullable=False),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("remaining_quota", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="active"),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "pricing_price_snapshots" not in tables:
        op.create_table(
            "pricing_price_snapshots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id"), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pricing_tier_rules.id"), nullable=True),
            sa.Column("package_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pricing_packages.id"), nullable=True),
            sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pricing_campaigns.id"), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
            sa.Column("amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
            sa.Column("duration_days", sa.Integer(), nullable=False, server_default="90"),
            sa.Column("snapshot_type", sa.String(length=20), nullable=False),
            sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    # Indexes
    if "pricing_tier_rules" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_tier_rules")}
        if "ix_pricing_tier_rules_scope" not in indexes:
            op.create_index("ix_pricing_tier_rules_scope", "pricing_tier_rules", ["scope", "is_active"])
        if "ix_pricing_tier_rules_tier" not in indexes:
            op.create_index("ix_pricing_tier_rules_tier", "pricing_tier_rules", ["scope", "tier_no"])

    if "pricing_packages" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_packages")}
        if "ix_pricing_packages_scope" not in indexes:
            op.create_index("ix_pricing_packages_scope", "pricing_packages", ["scope", "is_active"])

    if "user_package_subscriptions" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("user_package_subscriptions")}
        if "ix_user_package_sub_status" not in indexes:
            op.create_index("ix_user_package_sub_status", "user_package_subscriptions", ["user_id", "status"])
        if "ix_user_package_sub_ends" not in indexes:
            op.create_index("ix_user_package_sub_ends", "user_package_subscriptions", ["ends_at"])

    if "pricing_price_snapshots" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_price_snapshots")}
        if "ix_pricing_snapshot_user" not in indexes:
            op.create_index("ix_pricing_snapshot_user", "pricing_price_snapshots", ["user_id"])
        if "uq_pricing_snapshot_listing" not in indexes:
            op.create_index("uq_pricing_snapshot_listing", "pricing_price_snapshots", ["listing_id"], unique=True)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_price_snapshots" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_price_snapshots")}
        if "uq_pricing_snapshot_listing" in indexes:
            op.drop_index("uq_pricing_snapshot_listing", table_name="pricing_price_snapshots")
        if "ix_pricing_snapshot_user" in indexes:
            op.drop_index("ix_pricing_snapshot_user", table_name="pricing_price_snapshots")
        op.drop_table("pricing_price_snapshots")

    if "user_package_subscriptions" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("user_package_subscriptions")}
        if "ix_user_package_sub_ends" in indexes:
            op.drop_index("ix_user_package_sub_ends", table_name="user_package_subscriptions")
        if "ix_user_package_sub_status" in indexes:
            op.drop_index("ix_user_package_sub_status", table_name="user_package_subscriptions")
        op.drop_table("user_package_subscriptions")

    if "pricing_packages" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_packages")}
        if "ix_pricing_packages_scope" in indexes:
            op.drop_index("ix_pricing_packages_scope", table_name="pricing_packages")
        op.drop_table("pricing_packages")

    if "pricing_tier_rules" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_tier_rules")}
        if "ix_pricing_tier_rules_tier" in indexes:
            op.drop_index("ix_pricing_tier_rules_tier", table_name="pricing_tier_rules")
        if "ix_pricing_tier_rules_scope" in indexes:
            op.drop_index("ix_pricing_tier_rules_scope", table_name="pricing_tier_rules")
        op.drop_table("pricing_tier_rules")
