"""
P68: Add audit index for ops alert delivery metrics window + channel lookups
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p68_ops_alert_delivery_idx"
down_revision: Union[str, Sequence[str], None] = "p61_ui_dashboard_cfg"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INDEX_NAME = "ix_audit_logs_ops_alert_delivery_time_channel"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "audit_logs" not in tables:
        return

    existing_indexes = {idx.get("name") for idx in inspector.get_indexes("audit_logs")}
    if INDEX_NAME not in existing_indexes:
        op.create_index(
            INDEX_NAME,
            "audit_logs",
            ["created_at", "resource_id"],
            unique=False,
            postgresql_where=sa.text("action = 'ui_config_ops_alert_delivery'"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "audit_logs" not in tables:
        return

    existing_indexes = {idx.get("name") for idx in inspector.get_indexes("audit_logs")}
    if INDEX_NAME in existing_indexes:
        op.drop_index(INDEX_NAME, table_name="audit_logs")