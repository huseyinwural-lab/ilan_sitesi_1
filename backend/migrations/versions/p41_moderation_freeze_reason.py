"""
P41: system_settings moderation_freeze_reason
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p41_moderation_freeze_reason"
down_revision: Union[str, Sequence[str], None] = "p40_users_push_subs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "system_settings" in inspector.get_table_names():
        cols = _column_names(inspector, "system_settings")
        if "moderation_freeze_reason" not in cols:
            op.add_column(
                "system_settings",
                sa.Column("moderation_freeze_reason", sa.String(length=280), nullable=True),
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "system_settings" in inspector.get_table_names():
        cols = _column_names(inspector, "system_settings")
        if "moderation_freeze_reason" in cols:
            op.drop_column("system_settings", "moderation_freeze_reason")
