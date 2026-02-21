"""plans add period

Revision ID: 6a51163ba322
Revises: c7f6f91d6cd1
Create Date: 2026-02-21 17:17:56.801503

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a51163ba322'
down_revision: Union[str, Sequence[str], None] = 'c7f6f91d6cd1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("period", sa.String(length=20), nullable=False, server_default="monthly"))
    op.execute("UPDATE plans SET period='monthly' WHERE period IS NULL")

    op.drop_constraint("uq_plans_scope_country_slug", "plans", type_="unique")
    op.create_unique_constraint(
        "uq_plans_scope_country_slug_period",
        "plans",
        ["country_scope", "country_code", "slug", "period"],
    )
    op.create_index("ix_plans_period", "plans", ["period"])


def downgrade() -> None:
    op.drop_index("ix_plans_period", table_name="plans")
    op.drop_constraint("uq_plans_scope_country_slug_period", "plans", type_="unique")
    op.create_unique_constraint(
        "uq_plans_scope_country_slug",
        "plans",
        ["country_scope", "country_code", "slug"],
    )
    op.drop_column("plans", "period")
