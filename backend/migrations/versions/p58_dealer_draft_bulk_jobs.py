"""
P58: Dealer draft config revisions + category bulk async jobs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "p58_dealer_draft_bulk_jobs"
down_revision: Union[str, Sequence[str], None] = "p57_cat_order_stab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())

    if "category_bulk_jobs" not in tables:
        op.create_table(
            "category_bulk_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("idempotency_key", sa.String(length=128), nullable=False),
            sa.Column("action", sa.String(length=20), nullable=False),
            sa.Column("scope", sa.String(length=20), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
            sa.Column("request_payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("result_summary", sa.JSON(), nullable=True),
            sa.Column("log_entries", sa.JSON(), nullable=True),
            sa.Column("total_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("processed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("changed_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("unchanged_records", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
            sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("locked_by", sa.String(length=120), nullable=True),
            sa.Column("error_code", sa.String(length=80), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_async", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("idempotency_key", name="uq_category_bulk_jobs_idempotency_key"),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_status ON category_bulk_jobs (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_next_retry_at ON category_bulk_jobs (next_retry_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_locked_at ON category_bulk_jobs (locked_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_idempotency_key ON category_bulk_jobs (idempotency_key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_status_retry ON category_bulk_jobs (status, next_retry_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_category_bulk_jobs_created_at ON category_bulk_jobs (created_at)")

    if "dealer_config_revisions" not in tables:
        op.create_table(
            "dealer_config_revisions",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("scope_key", sa.String(length=32), nullable=False, server_default="GLOBAL"),
            sa.Column("state", sa.String(length=20), nullable=False, server_default="draft"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("revision_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("source_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("nav_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            sa.Column("module_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            sa.Column("meta_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("updated_by_email", sa.String(length=255), nullable=True),
            sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
    op.execute("CREATE INDEX IF NOT EXISTS ix_dealer_config_revisions_scope_key ON dealer_config_revisions (scope_key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dealer_config_revisions_state ON dealer_config_revisions (state)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dealer_config_revisions_is_active ON dealer_config_revisions (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dealer_config_revisions_scope_state ON dealer_config_revisions (scope_key, state)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dealer_config_revisions_scope_active ON dealer_config_revisions (scope_key, is_active)")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_dealer_config_active_draft_scope
        ON dealer_config_revisions (scope_key)
        WHERE state = 'draft' AND is_active = true
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_dealer_config_active_draft_scope")

    op.drop_index("ix_dealer_config_revisions_scope_active", table_name="dealer_config_revisions")
    op.drop_index("ix_dealer_config_revisions_scope_state", table_name="dealer_config_revisions")
    op.drop_index("ix_dealer_config_revisions_is_active", table_name="dealer_config_revisions")
    op.drop_index("ix_dealer_config_revisions_state", table_name="dealer_config_revisions")
    op.drop_index("ix_dealer_config_revisions_scope_key", table_name="dealer_config_revisions")
    op.drop_table("dealer_config_revisions")

    op.drop_index("ix_category_bulk_jobs_created_at", table_name="category_bulk_jobs")
    op.drop_index("ix_category_bulk_jobs_status_retry", table_name="category_bulk_jobs")
    op.drop_index("ix_category_bulk_jobs_idempotency_key", table_name="category_bulk_jobs")
    op.drop_index("ix_category_bulk_jobs_locked_at", table_name="category_bulk_jobs")
    op.drop_index("ix_category_bulk_jobs_next_retry_at", table_name="category_bulk_jobs")
    op.drop_index("ix_category_bulk_jobs_status", table_name="category_bulk_jobs")
    op.drop_table("category_bulk_jobs")