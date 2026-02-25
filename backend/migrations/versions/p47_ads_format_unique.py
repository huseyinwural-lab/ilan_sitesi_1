"""
P47: Ad format + single active ad per placement
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p47_ads_format_unique"
down_revision: Union[str, Sequence[str], None] = "p46_ad_campaigns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "advertisements" in tables:
        columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "format" not in columns:
            op.add_column("advertisements", sa.Column("format", sa.String(length=20), nullable=True))

        op.execute(
            """
            UPDATE advertisements
            SET format = CASE
                WHEN placement IN ('AD_CATEGORY_RIGHT', 'AD_LISTING_RIGHT') THEN 'vertical'
                WHEN placement = 'AD_IN_FEED' THEN 'square'
                ELSE 'horizontal'
            END
            WHERE format IS NULL
            """
        )

        op.execute(
            """
            WITH ranked AS (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY placement ORDER BY updated_at DESC NULLS LAST) AS rn
                FROM advertisements
                WHERE is_active = true
            )
            UPDATE advertisements
            SET is_active = false,
                updated_at = now()
            WHERE id IN (SELECT id FROM ranked WHERE rn > 1)
            """
        )

        existing_indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "uq_ads_active_placement" not in existing_indexes:
            op.create_index(
                "uq_ads_active_placement",
                "advertisements",
                ["placement"],
                unique=True,
                postgresql_where=sa.text("is_active")
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "advertisements" in tables:
        indexes = {idx["name"] for idx in inspector.get_indexes("advertisements")}
        if "uq_ads_active_placement" in indexes:
            op.drop_index("uq_ads_active_placement", table_name="advertisements")
        columns = {col["name"] for col in inspector.get_columns("advertisements")}
        if "format" in columns:
            op.drop_column("advertisements", "format")
