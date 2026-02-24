"""
P39: users + listings fields for SQL cutover
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'p39_users_listings_cutover'
down_revision: Union[str, Sequence[str], None] = 'p38_moderation_items'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "users" in inspector.get_table_names():
        cols = _column_names(inspector, "users")
        if "user_type" not in cols:
            op.add_column(
                "users",
                sa.Column("user_type", sa.String(length=20), nullable=False, server_default="individual"),
            )
        if "kyc_status" not in cols:
            op.add_column(
                "users",
                sa.Column("kyc_status", sa.String(length=20), nullable=False, server_default="none"),
            )
        if "is_phone_verified" not in cols:
            op.add_column(
                "users",
                sa.Column("is_phone_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            )
        if "trust_score" not in cols:
            op.add_column(
                "users",
                sa.Column("trust_score", sa.Float(), nullable=False, server_default=sa.text("0")),
            )

    if "listings" in inspector.get_table_names():
        cols = _column_names(inspector, "listings")
        if "current_step" not in cols:
            op.add_column(
                "listings",
                sa.Column("current_step", sa.Integer(), nullable=False, server_default=sa.text("1")),
            )
        if "completion_percentage" not in cols:
            op.add_column(
                "listings",
                sa.Column("completion_percentage", sa.Integer(), nullable=False, server_default=sa.text("0")),
            )
        if "user_type_snapshot" not in cols:
            op.add_column(
                "listings",
                sa.Column("user_type_snapshot", sa.String(length=20), nullable=True),
            )
        if "last_edited_at" not in cols:
            op.add_column(
                "listings",
                sa.Column("last_edited_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "moderated_at" not in cols:
            op.add_column(
                "listings",
                sa.Column("moderated_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "moderated_by" not in cols:
            op.add_column(
                "listings",
                sa.Column("moderated_by", postgresql.UUID(as_uuid=True), nullable=True),
            )
        if "rejected_reason" not in cols:
            op.add_column(
                "listings",
                sa.Column("rejected_reason", sa.Text(), nullable=True),
            )
        if "deleted_at" not in cols:
            op.add_column(
                "listings",
                sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
            )
        if "zip_code" not in cols:
            op.add_column(
                "listings",
                sa.Column("zip_code", sa.String(length=20), nullable=True),
            )
        if "latitude" not in cols:
            op.add_column(
                "listings",
                sa.Column("latitude", sa.Float(), nullable=True),
            )
        if "longitude" not in cols:
            op.add_column(
                "listings",
                sa.Column("longitude", sa.Float(), nullable=True),
            )
        if "location_accuracy" not in cols:
            op.add_column(
                "listings",
                sa.Column(
                    "location_accuracy",
                    sa.String(length=20),
                    nullable=False,
                    server_default="approximate",
                ),
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "listings" in inspector.get_table_names():
        cols = _column_names(inspector, "listings")
        for column_name in (
            "location_accuracy",
            "longitude",
            "latitude",
            "zip_code",
            "deleted_at",
            "rejected_reason",
            "moderated_by",
            "moderated_at",
            "last_edited_at",
            "user_type_snapshot",
            "completion_percentage",
            "current_step",
        ):
            if column_name in cols:
                op.drop_column("listings", column_name)

    if "users" in inspector.get_table_names():
        cols = _column_names(inspector, "users")
        for column_name in ("trust_score", "is_phone_verified", "kyc_status", "user_type"):
            if column_name in cols:
                op.drop_column("users", column_name)
