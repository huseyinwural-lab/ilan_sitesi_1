"""
P46: Ad campaigns + campaign_id on ads
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p46_ad_campaigns"
down_revision: Union[str, Sequence[str], None] = "p45_ad_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "ad_campaigns" not in tables:
        op.create_table(
            "ad_campaigns",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("advertiser", sa.String(length=200), nullable=True),
            sa.Column("budget", sa.Numeric(12, 2), nullable=True),
            sa.Column("currency", sa.String(length=3), nullable=False, server_default="EUR"),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    existing_campaign_indexes = set()
    if "ad_campaigns" in tables:
        existing_campaign_indexes = {idx["name"] for idx in inspector.get_indexes("ad_campaigns")}
    if "ix_ad_campaigns_status" not in existing_campaign_indexes:
        op.create_index("ix_ad_campaigns_status", "ad_campaigns", ["status"])
    if "ix_ad_campaigns_end_at" not in existing_campaign_indexes:
        op.create_index("ix_ad_campaigns_end_at", "ad_campaigns", ["end_at"])

    if "advertisements" in tables:
        ad_columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "campaign_id" not in ad_columns:
            op.add_column("advertisements", sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True))
            op.create_foreign_key(
                "fk_ads_campaign",
                "advertisements",
                "ad_campaigns",
                ["campaign_id"],
                ["id"],
                ondelete="SET NULL",
            )

        existing_ad_indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "ix_ads_campaign_id" not in existing_ad_indexes:
            op.create_index("ix_ads_campaign_id", "advertisements", ["campaign_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "advertisements" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "ix_ads_campaign_id" in indexes:
            op.drop_index("ix_ads_campaign_id", table_name="advertisements")
        columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "campaign_id" in columns:
            try:
                op.drop_constraint("fk_ads_campaign", "advertisements", type_="foreignkey")
            except Exception:
                pass
            op.drop_column("advertisements", "campaign_id")

    if "ad_campaigns" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("ad_campaigns")}
        if "ix_ad_campaigns_end_at" in indexes:
            op.drop_index("ix_ad_campaigns_end_at", table_name="ad_campaigns")
        if "ix_ad_campaigns_status" in indexes:
            op.drop_index("ix_ad_campaigns_status", table_name="ad_campaigns")
        op.drop_table("ad_campaigns")
