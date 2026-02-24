"""
P45: Ad analytics (impressions + clicks)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p45_ad_analytics"
down_revision: Union[str, Sequence[str], None] = "p44_site_content_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "ad_impressions" not in tables:
        op.create_table(
            "ad_impressions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("ad_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("advertisements.id", ondelete="CASCADE"), nullable=False),
            sa.Column("placement", sa.String(length=64), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ip_hash", sa.String(length=64), nullable=False),
            sa.Column("user_agent_hash", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "ad_clicks" not in tables:
        op.create_table(
            "ad_clicks",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("ad_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("advertisements.id", ondelete="CASCADE"), nullable=False),
            sa.Column("placement", sa.String(length=64), nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("ip_hash", sa.String(length=64), nullable=False),
            sa.Column("user_agent_hash", sa.String(length=64), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    existing_impression_indexes = set()
    if "ad_impressions" in tables:
        existing_impression_indexes = {idx["name"] for idx in inspector.get_indexes("ad_impressions")}
    if "ix_ad_impressions_ad_time" not in existing_impression_indexes:
        op.create_index("ix_ad_impressions_ad_time", "ad_impressions", ["ad_id", "created_at"])
    if "ix_ad_impressions_placement_time" not in existing_impression_indexes:
        op.create_index("ix_ad_impressions_placement_time", "ad_impressions", ["placement", "created_at"])
    if "ix_ad_impressions_dedup" not in existing_impression_indexes:
        op.create_index("ix_ad_impressions_dedup", "ad_impressions", ["ad_id", "ip_hash", "user_agent_hash", "created_at"])

    existing_click_indexes = set()
    if "ad_clicks" in tables:
        existing_click_indexes = {idx["name"] for idx in inspector.get_indexes("ad_clicks")}
    if "ix_ad_clicks_ad_time" not in existing_click_indexes:
        op.create_index("ix_ad_clicks_ad_time", "ad_clicks", ["ad_id", "created_at"])
    if "ix_ad_clicks_placement_time" not in existing_click_indexes:
        op.create_index("ix_ad_clicks_placement_time", "ad_clicks", ["placement", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ad_clicks_placement_time", table_name="ad_clicks")
    op.drop_index("ix_ad_clicks_ad_time", table_name="ad_clicks")
    op.drop_table("ad_clicks")

    op.drop_index("ix_ad_impressions_dedup", table_name="ad_impressions")
    op.drop_index("ix_ad_impressions_placement_time", table_name="ad_impressions")
    op.drop_index("ix_ad_impressions_ad_time", table_name="ad_impressions")
    op.drop_table("ad_impressions")
