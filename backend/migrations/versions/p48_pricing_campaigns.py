"""
P48: Pricing campaign policy
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p48_pricing_campaigns"
down_revision: Union[str, Sequence[str], None] = "p47_ads_format_unique"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_campaigns" not in tables:
        op.create_table(
            "pricing_campaigns",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("scope", sa.String(length=16), nullable=False, server_default="all"),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    existing_indexes = set()
    if "pricing_campaigns" in tables:
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaigns")}

    if "ix_pricing_campaigns_end_at" not in existing_indexes:
        op.create_index("ix_pricing_campaigns_end_at", "pricing_campaigns", ["end_at"])

    if "uq_pricing_campaign_active" not in existing_indexes:
        op.create_index(
            "uq_pricing_campaign_active",
            "pricing_campaigns",
            ["is_enabled"],
            unique=True,
            postgresql_where=sa.text("is_enabled")
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "pricing_campaigns" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("pricing_campaigns")}
        if "uq_pricing_campaign_active" in indexes:
            op.drop_index("uq_pricing_campaign_active", table_name="pricing_campaigns")
        if "ix_pricing_campaigns_end_at" in indexes:
            op.drop_index("ix_pricing_campaigns_end_at", table_name="pricing_campaigns")
        op.drop_table("pricing_campaigns")
