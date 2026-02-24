"""
P42: gdpr_exports table
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p42_gdpr_exports"
down_revision: Union[str, Sequence[str], None] = "p41_moderation_freeze_reason"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "gdpr_exports" not in inspector.get_table_names():
        op.create_table(
            "gdpr_exports",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("file_path", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_gdpr_exports_user_created", "gdpr_exports", ["user_id", "created_at"])
        op.create_index("ix_gdpr_exports_status", "gdpr_exports", ["status"])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "gdpr_exports" in inspector.get_table_names():
        op.drop_index("ix_gdpr_exports_status", table_name="gdpr_exports")
        op.drop_index("ix_gdpr_exports_user_created", table_name="gdpr_exports")
        op.drop_table("gdpr_exports")
