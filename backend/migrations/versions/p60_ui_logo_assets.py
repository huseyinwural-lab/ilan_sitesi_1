"""
P60: UI logo assets lifecycle table for replace/cleanup flow
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "p60_ui_logo_assets"
down_revision: Union[str, Sequence[str], None] = "p59_ui_designer_foundation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "ui_logo_assets" not in tables:
        op.create_table(
            "ui_logo_assets",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("asset_key", sa.String(length=255), nullable=False),
            sa.Column("asset_url", sa.String(length=512), nullable=False),
            sa.Column("segment", sa.String(length=16), nullable=False, server_default="corporate"),
            sa.Column("scope", sa.String(length=16), nullable=False, server_default="system"),
            sa.Column("scope_id", sa.String(length=64), nullable=True),
            sa.Column("config_type", sa.String(length=16), nullable=False, server_default="header"),
            sa.Column("is_replaced", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("replaced_by_asset_key", sa.String(length=255), nullable=True),
            sa.Column("replaced_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("delete_after", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("asset_key", name="uq_ui_logo_assets_asset_key"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_segment ON ui_logo_assets (segment)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_scope ON ui_logo_assets (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_scope_id ON ui_logo_assets (scope_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_config_type ON ui_logo_assets (config_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_is_replaced ON ui_logo_assets (is_replaced)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_is_deleted ON ui_logo_assets (is_deleted)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_delete_after ON ui_logo_assets (delete_after)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ui_logo_assets_scope_lookup ON ui_logo_assets (config_type, segment, scope, scope_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_scope_lookup")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_delete_after")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_is_deleted")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_is_replaced")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_config_type")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_scope_id")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_scope")
    op.execute("DROP INDEX IF EXISTS ix_ui_logo_assets_segment")
    op.drop_table("ui_logo_assets")
