"""
P43: Admin Final Guards (risk_level, ban_reason, discount_percent, quota constraints)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p43_admin_final_guards"
down_revision: Union[str, Sequence[str], None] = "p42_gdpr_exports"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

RISK_LEVEL_ENUM = sa.Enum("low", "medium", "high", name="risk_level")
QUOTA_MIN = 0
QUOTA_MAX = 10000


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {col["name"] for col in inspector.get_columns(table_name)}


def _constraint_exists(conn, name: str) -> bool:
    result = conn.execute(
        sa.text(
            """
            SELECT 1
            FROM pg_constraint
            WHERE conname = :name
            """
        ),
        {"name": name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # Enum type
    conn.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'risk_level') THEN
                    CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high');
                END IF;
            END$$;
            """
        )
    )

    if "users" in inspector.get_table_names():
        cols = _column_names(inspector, "users")
        if "risk_level" not in cols:
            op.add_column(
                "users",
                sa.Column(
                    "risk_level",
                    RISK_LEVEL_ENUM,
                    nullable=False,
                    server_default="low",
                ),
            )
            conn.execute(sa.text("UPDATE users SET risk_level='low' WHERE risk_level IS NULL"))
            op.alter_column("users", "risk_level", server_default=None)
        if "ban_reason" not in cols:
            op.add_column("users", sa.Column("ban_reason", sa.Text(), nullable=True))

        if not _constraint_exists(conn, "ck_users_ban_reason_required"):
            op.create_check_constraint(
                "ck_users_ban_reason_required",
                "users",
                "status <> 'suspended' OR (ban_reason IS NOT NULL AND btrim(ban_reason) <> '')",
            )

        if not _constraint_exists(conn, "ck_users_suspension_until_status"):
            op.create_check_constraint(
                "ck_users_suspension_until_status",
                "users",
                "suspension_until IS NULL OR status = 'suspended'",
            )

    if "plans" in inspector.get_table_names():
        if not _constraint_exists(conn, "ck_plans_quota_range"):
            op.create_check_constraint(
                "ck_plans_quota_range",
                "plans",
                f"listing_quota BETWEEN {QUOTA_MIN} AND {QUOTA_MAX} AND showcase_quota BETWEEN {QUOTA_MIN} AND {QUOTA_MAX}",
            )

    if "subscription_plans" in inspector.get_table_names():
        cols = _column_names(inspector, "subscription_plans")
        if "discount_percent" not in cols:
            op.add_column(
                "subscription_plans",
                sa.Column("discount_percent", sa.Numeric(5, 2), nullable=False, server_default="0"),
            )
            op.alter_column("subscription_plans", "discount_percent", server_default=None)

        if not _constraint_exists(conn, "ck_subscription_plans_discount_percent"):
            op.create_check_constraint(
                "ck_subscription_plans_discount_percent",
                "subscription_plans",
                "discount_percent BETWEEN 0 AND 100",
            )

        if not _constraint_exists(conn, "ck_subscription_plans_limits_range"):
            op.create_check_constraint(
                "ck_subscription_plans_limits_range",
                "subscription_plans",
                f"((limits->>'listing')::int BETWEEN {QUOTA_MIN} AND {QUOTA_MAX}) AND ((limits->>'showcase')::int BETWEEN {QUOTA_MIN} AND {QUOTA_MAX})",
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "subscription_plans" in inspector.get_table_names():
        if _constraint_exists(conn, "ck_subscription_plans_limits_range"):
            op.drop_constraint("ck_subscription_plans_limits_range", "subscription_plans", type_="check")
        if _constraint_exists(conn, "ck_subscription_plans_discount_percent"):
            op.drop_constraint("ck_subscription_plans_discount_percent", "subscription_plans", type_="check")
        cols = _column_names(inspector, "subscription_plans")
        if "discount_percent" in cols:
            op.drop_column("subscription_plans", "discount_percent")

    if "plans" in inspector.get_table_names():
        if _constraint_exists(conn, "ck_plans_quota_range"):
            op.drop_constraint("ck_plans_quota_range", "plans", type_="check")

    if "users" in inspector.get_table_names():
        if _constraint_exists(conn, "ck_users_suspension_until_status"):
            op.drop_constraint("ck_users_suspension_until_status", "users", type_="check")
        if _constraint_exists(conn, "ck_users_ban_reason_required"):
            op.drop_constraint("ck_users_ban_reason_required", "users", type_="check")
        cols = _column_names(inspector, "users")
        if "ban_reason" in cols:
            op.drop_column("users", "ban_reason")
        if "risk_level" in cols:
            op.drop_column("users", "risk_level")

    # Drop enum type if no longer used
    conn.execute(sa.text("DROP TYPE IF EXISTS risk_level"))
