"""Add deleted_at to dealer_listings

Revision ID: aa12b9c8d7e1
Revises: 9ccf26034bea
Create Date: 2026-02-21

"""
from alembic import op
import sqlalchemy as sa

revision = "aa12b9c8d7e1"
down_revision = "9ccf26034bea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("dealer_listings", sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("dealer_listings", "deleted_at")
