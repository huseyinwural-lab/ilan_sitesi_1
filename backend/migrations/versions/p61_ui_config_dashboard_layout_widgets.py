"""
P61: Add dashboard layout/widgets columns to ui_configs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "p61_ui_dashboard_cfg"
down_revision: Union[str, Sequence[str], None] = "p60_ui_logo_assets"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "ui_configs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("ui_configs")}

    if "layout" not in columns:
        op.add_column(
            "ui_configs",
            sa.Column(
                "layout",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )

    if "widgets" not in columns:
        op.add_column(
            "ui_configs",
            sa.Column(
                "widgets",
                postgresql.JSONB(astext_type=sa.Text()),
                nullable=False,
                server_default=sa.text("'[]'::jsonb"),
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "ui_configs" not in tables:
        return

    columns = {column["name"] for column in inspector.get_columns("ui_configs")}
    if "widgets" in columns:
        op.drop_column("ui_configs", "widgets")
    if "layout" in columns:
        op.drop_column("ui_configs", "layout")
