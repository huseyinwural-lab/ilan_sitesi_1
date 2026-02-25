"""
P54: Vehicle master data import jobs + trims
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "p54_vehicle_master_import_jobs"
down_revision: Union[str, Sequence[str], None] = "p53_site_theme_soft_delete"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "vehicle_trims" not in tables:
        op.create_table(
            "vehicle_trims",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("make_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("model_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("slug", sa.String(length=160), nullable=False),
            sa.Column("source", sa.String(length=50), nullable=True),
            sa.Column("source_ref", sa.String(length=120), nullable=True),
            sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.ForeignKeyConstraint(["make_id"], ["vehicle_makes.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["model_id"], ["vehicle_models.id"], ondelete="CASCADE"),
        )
        op.create_index("ix_vehicle_trims_make_id", "vehicle_trims", ["make_id"])
        op.create_index("ix_vehicle_trims_model_id", "vehicle_trims", ["model_id"])
        op.create_index("ix_vehicle_trims_year", "vehicle_trims", ["year"])
        op.create_index("ix_vehicle_trim_source_ref", "vehicle_trims", ["source_ref"])
        op.create_unique_constraint(
            "uq_vehicle_trim_identity",
            "vehicle_trims",
            ["make_id", "model_id", "year", "slug"],
        )

    if "vehicle_import_jobs" not in tables:
        op.create_table(
            "vehicle_import_jobs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="queued"),
            sa.Column("source", sa.String(length=20), nullable=False),
            sa.Column("dry_run", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column("request_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("error_log", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("log_entries", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("total_records", sa.Integer(), nullable=True),
            sa.Column("processed_records", sa.Integer(), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column("created_by_email", sa.String(length=255), nullable=True),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_vehicle_import_jobs_created_at", "vehicle_import_jobs", ["created_at"])
        op.create_index("ix_vehicle_import_jobs_status", "vehicle_import_jobs", ["status"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "vehicle_import_jobs" in tables:
        op.drop_index("ix_vehicle_import_jobs_status", table_name="vehicle_import_jobs")
        op.drop_index("ix_vehicle_import_jobs_created_at", table_name="vehicle_import_jobs")
        op.drop_table("vehicle_import_jobs")

    if "vehicle_trims" in tables:
        op.drop_constraint("uq_vehicle_trim_identity", "vehicle_trims", type_="unique")
        op.drop_index("ix_vehicle_trim_source_ref", table_name="vehicle_trims")
        op.drop_index("ix_vehicle_trims_year", table_name="vehicle_trims")
        op.drop_index("ix_vehicle_trims_model_id", table_name="vehicle_trims")
        op.drop_index("ix_vehicle_trims_make_id", table_name="vehicle_trims")
        op.drop_table("vehicle_trims")
