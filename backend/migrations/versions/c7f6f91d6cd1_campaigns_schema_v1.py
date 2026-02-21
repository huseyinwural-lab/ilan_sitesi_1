"""campaigns schema v1

Revision ID: c7f6f91d6cd1
Revises: 5710cb21ddfd
Create Date: 2026-02-21 17:17:02.725955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7f6f91d6cd1'
down_revision: Union[str, Sequence[str], None] = '5710cb21ddfd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("campaigns", sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("campaigns", sa.Column("budget_currency", sa.String(length=5), nullable=True))
    op.add_column("campaigns", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column("campaigns", sa.Column("rules_json", sa.JSON(), nullable=True))

    op.execute("UPDATE campaigns SET status='ended' WHERE status='archived'")
    op.execute("UPDATE campaigns SET country_code='DE' WHERE country_code IS NULL")
    op.execute("UPDATE campaigns SET notes=description WHERE description IS NOT NULL")

    op.drop_index("ix_campaigns_type", table_name="campaigns")
    op.drop_index("ix_campaigns_priority", table_name="campaigns")
    op.drop_index("ix_campaigns_status", table_name="campaigns")
    op.drop_index("ix_campaigns_country_code", table_name="campaigns")

    op.drop_column("campaigns", "type")
    op.drop_column("campaigns", "country_scope")
    op.drop_column("campaigns", "description")
    op.drop_column("campaigns", "priority")
    op.drop_column("campaigns", "duration_days")
    op.drop_column("campaigns", "quota_count")
    op.drop_column("campaigns", "price_amount")
    op.drop_column("campaigns", "currency_code")
    op.drop_column("campaigns", "created_by_admin_id")

    op.alter_column("campaigns", "country_code", nullable=False)

    op.create_index("ix_campaigns_country_status", "campaigns", ["country_code", "status"])
    op.create_index("ix_campaigns_created_at", "campaigns", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_campaigns_created_at", table_name="campaigns")
    op.drop_index("ix_campaigns_country_status", table_name="campaigns")

    op.alter_column("campaigns", "country_code", nullable=True)

    op.add_column("campaigns", sa.Column("created_by_admin_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("campaigns", sa.Column("currency_code", sa.String(length=5), nullable=True))
    op.add_column("campaigns", sa.Column("price_amount", sa.Numeric(12, 2), nullable=True))
    op.add_column("campaigns", sa.Column("quota_count", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("duration_days", sa.Integer(), nullable=True))
    op.add_column("campaigns", sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"))
    op.add_column("campaigns", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("campaigns", sa.Column("country_scope", sa.String(length=20), nullable=False, server_default="global"))
    op.add_column("campaigns", sa.Column("type", sa.String(length=20), nullable=False, server_default="individual"))

    op.drop_column("campaigns", "rules_json")
    op.drop_column("campaigns", "notes")
    op.drop_column("campaigns", "budget_currency")
    op.drop_column("campaigns", "budget_amount")

    op.create_index("ix_campaigns_type", "campaigns", ["type"])
    op.create_index("ix_campaigns_status", "campaigns", ["status"])
    op.create_index("ix_campaigns_country_code", "campaigns", ["country_code"])
    op.create_index("ix_campaigns_priority", "campaigns", ["priority"])
