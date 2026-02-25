"""
P52: Site header config
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p52_site_header_config"
down_revision: Union[str, Sequence[str], None] = "p51_drop_campaign_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "site_header_config" not in inspector.get_table_names():
        op.create_table(
            "site_header_config",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("logo_path", sa.String(length=255), nullable=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    indexes = {idx["name"] for idx in inspector.get_indexes("site_header_config")}
    if "uq_site_header_config_active" not in indexes:
        op.create_index(
            "uq_site_header_config_active",
            "site_header_config",
            ["is_active"],
            unique=True,
            postgresql_where=sa.text("is_active = true"),
        )
    if "ix_site_header_config_updated_at" not in indexes:
        op.create_index("ix_site_header_config_updated_at", "site_header_config", ["updated_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "site_header_config" in inspector.get_table_names():
        indexes = {idx["name"] for idx in inspector.get_indexes("site_header_config")}
        if "uq_site_header_config_active" in indexes:
            op.drop_index("uq_site_header_config_active", table_name="site_header_config")
        if "ix_site_header_config_updated_at" in indexes:
            op.drop_index("ix_site_header_config_updated_at", table_name="site_header_config")
        op.drop_table("site_header_config")
