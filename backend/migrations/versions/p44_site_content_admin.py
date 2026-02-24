"""
P44: Site content (header, ads, doping, footer, info pages)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p44_site_content_admin"
down_revision: Union[str, Sequence[str], None] = "p43_admin_final_guards"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "site_header_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("logo_url", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "advertisements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("placement", sa.String(length=64), nullable=False),
        sa.Column("asset_url", sa.Text(), nullable=True),
        sa.Column("target_url", sa.Text(), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_ads_placement_active", "advertisements", ["placement", "is_active"])
    op.create_index("ix_ads_placement_priority", "advertisements", ["placement", "priority"])

    op.create_table(
        "doping_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="requested"),
        sa.Column("placement_home", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("placement_category", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_doping_listing_status", "doping_requests", ["listing_id", "status"])
    op.create_index("ix_doping_end_at", "doping_requests", ["end_at"])

    op.create_table(
        "footer_layouts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("layout", postgresql.JSON(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "info_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("title_tr", sa.String(length=200), nullable=False),
        sa.Column("title_de", sa.String(length=200), nullable=False),
        sa.Column("title_fr", sa.String(length=200), nullable=False),
        sa.Column("content_tr", sa.Text(), nullable=False),
        sa.Column("content_de", sa.Text(), nullable=False),
        sa.Column("content_fr", sa.Text(), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_info_pages_published", "info_pages", ["is_published"])
    op.create_unique_constraint("uq_info_pages_slug", "info_pages", ["slug"])


def downgrade() -> None:
    op.drop_constraint("uq_info_pages_slug", "info_pages", type_="unique")
    op.drop_index("ix_info_pages_published", table_name="info_pages")
    op.drop_table("info_pages")

    op.drop_table("footer_layouts")

    op.drop_index("ix_doping_end_at", table_name="doping_requests")
    op.drop_index("ix_doping_listing_status", table_name="doping_requests")
    op.drop_table("doping_requests")

    op.drop_index("ix_ads_placement_priority", table_name="advertisements")
    op.drop_index("ix_ads_placement_active", table_name="advertisements")
    op.drop_table("advertisements")

    op.drop_table("site_header_settings")
