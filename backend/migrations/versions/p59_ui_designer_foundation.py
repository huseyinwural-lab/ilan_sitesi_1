"""
P59: UI Designer foundation tables (ui_configs, ui_themes, ui_theme_assignments)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "p59_ui_designer_foundation"
down_revision: Union[str, Sequence[str], None] = "p58_dealer_draft_bulk_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "ui_configs" not in tables:
        op.create_table(
            "ui_configs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="draft"),
            sa.Column("segment", sa.String(length=16), nullable=False, server_default="individual"),
            sa.Column("scope", sa.String(length=16), nullable=False, server_default="system"),
            sa.Column("scope_id", sa.String(length=64), nullable=True),
            sa.Column("config_type", sa.String(length=16), nullable=False),
            sa.Column("config_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint(
                "config_type",
                "segment",
                "scope",
                "scope_id",
                "version",
                name="uq_ui_configs_version_scope",
            ),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_configs_status ON ui_configs (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_configs_segment ON ui_configs (segment)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_configs_scope ON ui_configs (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_configs_scope_id ON ui_configs (scope_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_configs_config_type ON ui_configs (config_type)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_ui_configs_effective_lookup ON ui_configs (config_type, segment, scope, scope_id, status, version)"
    )

    if "ui_themes" not in tables:
        op.create_table(
            "ui_themes",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("tokens", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("name", name="uq_ui_themes_name"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_themes_is_active ON ui_themes (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_themes_name ON ui_themes (name)")

    if "ui_theme_assignments" not in tables:
        op.create_table(
            "ui_theme_assignments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ui_themes.id"), nullable=False),
            sa.Column("scope", sa.String(length=16), nullable=False, server_default="system"),
            sa.Column("scope_id", sa.String(length=64), nullable=True),
            sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("assigned_by_email", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("scope", "scope_id", name="uq_ui_theme_assignments_scope"),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_theme_assignments_theme_id ON ui_theme_assignments (theme_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_theme_assignments_scope ON ui_theme_assignments (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_ui_theme_assignments_scope_id ON ui_theme_assignments (scope_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_ui_theme_assignments_scope_id")
    op.execute("DROP INDEX IF EXISTS ix_ui_theme_assignments_scope")
    op.execute("DROP INDEX IF EXISTS ix_ui_theme_assignments_theme_id")
    op.execute("DROP INDEX IF EXISTS ix_ui_themes_name")
    op.execute("DROP INDEX IF EXISTS ix_ui_themes_is_active")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_effective_lookup")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_config_type")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_scope_id")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_scope")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_segment")
    op.execute("DROP INDEX IF EXISTS ix_ui_configs_status")

    op.drop_table("ui_theme_assignments")
    op.drop_table("ui_themes")
    op.drop_table("ui_configs")
