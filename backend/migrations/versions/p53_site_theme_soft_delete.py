"""
P53: Site theme config + ad soft delete
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p53_site_theme_and_ad_soft_delete"
down_revision: Union[str, Sequence[str], None] = "p52_site_header_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "site_theme_configs" not in tables:
        op.create_table(
            "site_theme_configs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )

    if "advertisements" in tables:
        columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "is_deleted" not in columns:
            op.add_column(
                "advertisements",
                sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            )
        if "deleted_at" not in columns:
            op.add_column("advertisements", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))

        indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "ix_ads_is_deleted" not in indexes:
            op.create_index("ix_ads_is_deleted", "advertisements", ["is_deleted"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "advertisements" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "ix_ads_is_deleted" in indexes:
            op.drop_index("ix_ads_is_deleted", table_name="advertisements")
        columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "deleted_at" in columns:
            op.drop_column("advertisements", "deleted_at")
        if "is_deleted" in columns:
            op.drop_column("advertisements", "is_deleted")

    if "site_theme_configs" in tables:
        op.drop_table("site_theme_configs")
