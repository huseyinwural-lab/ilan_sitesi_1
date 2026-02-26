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
    op.create_index("ix_category_bulk_jobs_status", "category_bulk_jobs", ["status"], unique=False)
    op.create_index("ix_category_bulk_jobs_next_retry_at", "category_bulk_jobs", ["next_retry_at"], unique=False)
    op.create_index("ix_category_bulk_jobs_locked_at", "category_bulk_jobs", ["locked_at"], unique=False)
    op.create_index("ix_category_bulk_jobs_idempotency_key", "category_bulk_jobs", ["idempotency_key"], unique=False)
    op.create_index("ix_category_bulk_jobs_status_retry", "category_bulk_jobs", ["status", "next_retry_at"], unique=False)
    op.create_index("ix_category_bulk_jobs_created_at", "category_bulk_jobs", ["created_at"], unique=False)

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
    op.create_index("ix_dealer_config_revisions_scope_key", "dealer_config_revisions", ["scope_key"], unique=False)
    op.create_index("ix_dealer_config_revisions_state", "dealer_config_revisions", ["state"], unique=False)
    op.create_index("ix_dealer_config_revisions_is_active", "dealer_config_revisions", ["is_active"], unique=False)
    op.create_index("ix_dealer_config_revisions_scope_state", "dealer_config_revisions", ["scope_key", "state"], unique=False)
    op.create_index("ix_dealer_config_revisions_scope_active", "dealer_config_revisions", ["scope_key", "is_active"], unique=False)
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