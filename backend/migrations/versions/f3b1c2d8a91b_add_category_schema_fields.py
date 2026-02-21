"""Add category schema fields

Revision ID: f3b1c2d8a91b
Revises: 9ccf26034bea
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f3b1c2d8a91b"
down_revision = "9ccf26034bea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("categories", sa.Column("country_code", sa.String(length=5), nullable=True))
    op.add_column("categories", sa.Column("hierarchy_complete", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("categories", sa.Column("form_schema", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_index("ix_categories_country_code", "categories", ["country_code"], unique=False)

    op.create_table(
        "category_schema_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("categories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("schema_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_by_role", sa.String(length=50), nullable=True),
        sa.Column("created_by_email", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_category_schema_versions_category", "category_schema_versions", ["category_id", "version"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_category_schema_versions_category", table_name="category_schema_versions")
    op.drop_table("category_schema_versions")

    op.drop_index("ix_categories_country_code", table_name="categories")
    op.drop_column("categories", "form_schema")
    op.drop_column("categories", "hierarchy_complete")
    op.drop_column("categories", "country_code")
