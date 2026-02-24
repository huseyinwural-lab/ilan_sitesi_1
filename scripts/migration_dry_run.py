#!/usr/bin/env python3
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import create_engine, text

REQUIRED_TABLES = [
    "users",
    "subscription_plans",
    "plans",
    "user_subscriptions",
    "listings",
    "audit_logs",
]

EXPECTED_COLUMNS = [
    {
        "table": "users",
        "column": "risk_level",
        "data_type": "USER-DEFINED",
        "udt_name": "risk_level",
        "required_pre": False,
    },
    {
        "table": "users",
        "column": "ban_reason",
        "data_type": "text",
        "udt_name": None,
        "required_pre": False,
    },
    {
        "table": "users",
        "column": "suspension_until",
        "data_type": "timestamp with time zone",
        "udt_name": None,
        "required_pre": True,
    },
    {
        "table": "plans",
        "column": "listing_quota",
        "data_type": "integer",
        "udt_name": None,
        "required_pre": True,
    },
    {
        "table": "plans",
        "column": "showcase_quota",
        "data_type": "integer",
        "udt_name": None,
        "required_pre": True,
    },
    {
        "table": "subscription_plans",
        "column": "limits",
        "data_type": "json",
        "udt_name": None,
        "required_pre": True,
        "alt_types": {"jsonb"},
    },
    {
        "table": "subscription_plans",
        "column": "discount_percent",
        "data_type": "numeric",
        "udt_name": None,
        "required_pre": False,
    },
]

EXPECTED_INDEXES = {
    "plans": [
        "ix_plans_country_scope",
        "ix_plans_country_code",
        "ix_plans_period",
        "ix_plans_active_flag",
        "ix_plans_archived_at",
    ],
    "user_subscriptions": [
        "ix_user_subscriptions_user",
        "ix_user_subscriptions_status",
    ],
}

RISK_LEVEL_ALLOWED = {"low", "medium", "high"}

MIGRATION_QUOTA_MIN = int(os.environ.get("MIGRATION_QUOTA_MIN", "0"))
MIGRATION_QUOTA_MAX = int(os.environ.get("MIGRATION_QUOTA_MAX", "10000"))
MIGRATION_DRY_RUN_AUDIT = os.environ.get("MIGRATION_DRY_RUN_AUDIT", "0") == "1"

SNAPSHOT_PATH = os.environ.get("MIGRATION_DRY_RUN_SNAPSHOT", "/tmp/migration_dry_run_snapshot.json")


def _format_issue(label: str) -> str:
    return f"- {label}"


def _load_db_url() -> str:
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("[MIGRATION-DRY-RUN] FAIL: DATABASE_URL is not set")
        sys.exit(2)
    return db_url


def _connect_engine(db_url: str):
    ssl_mode = os.environ.get("DB_SSL_MODE")
    connect_args = {"sslmode": ssl_mode} if ssl_mode else {}
    return create_engine(db_url, pool_pre_ping=True, connect_args=connect_args)


def _fetch_table_set(conn) -> set[str]:
    result = conn.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
    )
    return {row[0] for row in result}


def _fetch_columns(conn, table: str) -> Dict[str, Dict[str, str]]:
    result = conn.execute(
        text(
            """
            SELECT column_name, data_type, udt_name, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = :table
            """
        ),
        {"table": table},
    )
    columns = {}
    for row in result:
        columns[row[0]] = {
            "data_type": row[1],
            "udt_name": row[2],
            "is_nullable": row[3],
        }
    return columns


def _fetch_indexes(conn, table: str) -> set[str]:
    result = conn.execute(
        text(
            """
            SELECT indexname
            FROM pg_indexes
            WHERE schemaname = 'public' AND tablename = :table
            """
        ),
        {"table": table},
    )
    return {row[0] for row in result}


def _count(conn, query: str, params: Dict[str, object] | None = None) -> int:
    result = conn.execute(text(query), params or {})
    return int(result.scalar() or 0)


def _write_audit_log(engine, status: str, blocking: List[str], warnings: List[str], created_at) -> None:
    metadata = {
        "status": status,
        "blocking_count": len(blocking),
        "warnings_count": len(warnings),
        "snapshot_path": SNAPSHOT_PATH,
        "blocking": blocking,
        "warnings": warnings,
    }
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO audit_logs
                (id, user_email, action, resource_type, resource_id, metadata_info, created_at)
                VALUES
                (:id, :user_email, :action, :resource_type, :resource_id, CAST(:metadata_info AS JSONB), :created_at)
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "user_email": "system@platform.com",
                "action": "MIGRATION_DRY_RUN",
                "resource_type": "migration",
                "resource_id": "af-sprint1",
                "metadata_info": json.dumps(metadata),
                "created_at": created_at,
            },
        )



def main() -> int:
    timestamp = datetime.now(timezone.utc).isoformat()
    blocking: List[str] = []
    warnings: List[str] = []

    db_url = _load_db_url()
    engine = _connect_engine(db_url)

    try:
        with engine.connect() as conn:
            tables = _fetch_table_set(conn)

            missing_tables = [table for table in REQUIRED_TABLES if table not in tables]
            if missing_tables:
                for table in missing_tables:
                    blocking.append(f"Missing table: {table}")

            for spec in EXPECTED_COLUMNS:
                table = spec["table"]
                column = spec["column"]
                if table not in tables:
                    continue
                columns = _fetch_columns(conn, table)
                if column not in columns:
                    if spec.get("required_pre", False):
                        blocking.append(f"Missing required column: {table}.{column}")
                    else:
                        warnings.append(f"Column not present yet (expected via migration): {table}.{column}")
                    continue

                data_type = columns[column]["data_type"]
                udt_name = columns[column]["udt_name"]
                expected_type = spec["data_type"]
                alt_types = spec.get("alt_types", set())
                if data_type != expected_type and data_type not in alt_types:
                    blocking.append(
                        f"Column type mismatch for {table}.{column}: {data_type} (expected {expected_type})"
                    )
                if expected_type == "USER-DEFINED" and spec.get("udt_name"):
                    if udt_name != spec["udt_name"]:
                        blocking.append(
                            f"Enum type mismatch for {table}.{column}: {udt_name} (expected {spec['udt_name']})"
                        )

            # Foreign key integrity
            if "user_subscriptions" in tables and "users" in tables:
                orphan_users = _count(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM user_subscriptions s
                    LEFT JOIN users u ON s.user_id = u.id
                    WHERE u.id IS NULL
                    """,
                )
                if orphan_users:
                    blocking.append(f"FK integrity failure: user_subscriptions.user_id ({orphan_users} orphans)")

            if "user_subscriptions" in tables and "plans" in tables:
                orphan_plans = _count(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM user_subscriptions s
                    LEFT JOIN plans p ON s.plan_id = p.id
                    WHERE p.id IS NULL
                    """,
                )
                if orphan_plans:
                    blocking.append(f"FK integrity failure: user_subscriptions.plan_id ({orphan_plans} orphans)")

            # Null/constraint checks
            if "users" in tables:
                columns = _fetch_columns(conn, "users")
                if "risk_level" in columns:
                    null_risk = _count(conn, "SELECT COUNT(*) FROM users WHERE risk_level IS NULL")
                    if null_risk:
                        blocking.append(f"Null risk_level values: {null_risk}")

                    invalid_risk = _count(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM users
                        WHERE risk_level IS NOT NULL
                          AND risk_level NOT IN :allowed
                        """,
                        {"allowed": tuple(RISK_LEVEL_ALLOWED)},
                    )
                    if invalid_risk:
                        blocking.append(f"Invalid risk_level values: {invalid_risk}")
                else:
                    warnings.append("risk_level column missing; enum validation skipped")

                if "ban_reason" in columns:
                    missing_reason = _count(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM users
                        WHERE status = 'suspended'
                          AND (ban_reason IS NULL OR btrim(ban_reason) = '')
                        """,
                    )
                    if missing_reason:
                        blocking.append(f"Suspended users without ban_reason: {missing_reason}")
                else:
                    warnings.append("ban_reason column missing; suspension reason check skipped")

                if "suspension_until" in columns:
                    invalid_suspension = _count(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM users
                        WHERE suspension_until IS NOT NULL
                          AND status != 'suspended'
                        """,
                    )
                    if invalid_suspension:
                        warnings.append(
                            f"suspension_until set for non-suspended users: {invalid_suspension}"
                        )

            if "plans" in tables:
                out_of_range = _count(
                    conn,
                    """
                    SELECT COUNT(*)
                    FROM plans
                    WHERE listing_quota < :min_q
                       OR listing_quota > :max_q
                       OR showcase_quota < :min_q
                       OR showcase_quota > :max_q
                    """,
                    {"min_q": MIGRATION_QUOTA_MIN, "max_q": MIGRATION_QUOTA_MAX},
                )
                if out_of_range:
                    blocking.append(f"Plan quotas outside range: {out_of_range}")

            if "subscription_plans" in tables:
                columns = _fetch_columns(conn, "subscription_plans")
                if "limits" in columns:
                    limit_violations = _count(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM subscription_plans
                        WHERE (limits->>'listing')::int < :min_q
                           OR (limits->>'listing')::int > :max_q
                           OR (limits->>'showcase')::int < :min_q
                           OR (limits->>'showcase')::int > :max_q
                        """,
                        {"min_q": MIGRATION_QUOTA_MIN, "max_q": MIGRATION_QUOTA_MAX},
                    )
                    if limit_violations:
                        blocking.append(f"subscription_plans.limits outside range: {limit_violations}")
                else:
                    warnings.append("subscription_plans.limits missing; quota JSON check skipped")

                if "discount_percent" in columns:
                    discount_violations = _count(
                        conn,
                        """
                        SELECT COUNT(*)
                        FROM subscription_plans
                        WHERE discount_percent < 0 OR discount_percent > 100
                        """,
                    )
                    if discount_violations:
                        blocking.append(f"discount_percent outside 0-100: {discount_violations}")
                else:
                    warnings.append("discount_percent column missing; discount guard skipped")

            # Index checks
            for table, index_list in EXPECTED_INDEXES.items():
                if table not in tables:
                    continue
                indexes = _fetch_indexes(conn, table)
                for idx in index_list:
                    if idx not in indexes:
                        warnings.append(f"Missing index: {idx} on {table}")

            # Row count delta
            row_counts = {}
            for table in REQUIRED_TABLES:
                if table in tables:
                    row_counts[table] = _count(conn, f"SELECT COUNT(*) FROM {table}")

            snapshot_path = SNAPSHOT_PATH
            if os.path.exists(snapshot_path):
                try:
                    previous = json.loads(open(snapshot_path, "r", encoding="utf-8").read())
                except Exception:
                    previous = {}
                for table, count in row_counts.items():
                    previous_count = int(previous.get(table, count))
                    delta = count - previous_count
                    if delta != 0:
                        warnings.append(f"Row count delta {table}: {previous_count} -> {count} (delta {delta})")
            else:
                warnings.append("No previous snapshot found; created new snapshot file")
                with open(snapshot_path, "w", encoding="utf-8") as handle:
                    json.dump(row_counts, handle, indent=2)

    except Exception as exc:
        print(f"[MIGRATION-DRY-RUN] FAIL: {exc}")
        return 2

    status = "PASS" if not blocking else "FAIL"

    if MIGRATION_DRY_RUN_AUDIT:
        try:
            _write_audit_log(engine, status, blocking, warnings, timestamp)
        except Exception as exc:
            blocking.append(f"Audit log write failed: {exc}")
            status = "FAIL"

    print(f"[MIGRATION-DRY-RUN] RESULT: {status}")
    print(f"Timestamp: {timestamp}")
    print(f"Blocking Issues: {len(blocking)}")
    for issue in blocking:
        print(_format_issue(issue))
    print(f"Warnings: {len(warnings)}")
    for warning in warnings:
        print(_format_issue(warning))

    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    sys.exit(main())
