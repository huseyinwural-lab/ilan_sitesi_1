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
    op.create_index("ix_ad_impressions_ad_time", "ad_impressions", ["ad_id", "created_at"])
    op.create_index("ix_ad_impressions_placement_time", "ad_impressions", ["placement", "created_at"])
    op.create_index("ix_ad_impressions_dedup", "ad_impressions", ["ad_id", "ip_hash", "user_agent_hash", "created_at"])

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
    op.create_index("ix_ad_clicks_ad_time", "ad_clicks", ["ad_id", "created_at"])
    op.create_index("ix_ad_clicks_placement_time", "ad_clicks", ["placement", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ad_clicks_placement_time", table_name="ad_clicks")
    op.drop_index("ix_ad_clicks_ad_time", table_name="ad_clicks")
    op.drop_table("ad_clicks")

    op.drop_index("ix_ad_impressions_dedup", table_name="ad_impressions")
    op.drop_index("ix_ad_impressions_placement_time", table_name="ad_impressions")
    op.drop_index("ix_ad_impressions_ad_time", table_name="ad_impressions")
    op.drop_table("ad_impressions")
