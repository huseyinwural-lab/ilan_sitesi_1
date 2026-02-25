"""
P55: Category ordering constraints
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "p55_category_ordering_constraints"
down_revision: Union[str, Sequence[str], None] = "p54_vehicle_master_import_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, parent_id
            FROM categories
            WHERE is_deleted = false
            ORDER BY parent_id NULLS FIRST, sort_order ASC, created_at ASC
            """
        )
    ).fetchall()

    current_parent = object()
    counter = 0
    for row in rows:
        if row.parent_id != current_parent:
            current_parent = row.parent_id
            counter = 1
        bind.execute(
            sa.text("UPDATE categories SET sort_order = :order WHERE id = :id"),
            {"order": counter, "id": row.id},
        )
        counter += 1

    op.create_index(
        "uq_categories_parent_sort",
        "categories",
        [sa.text("coalesce(parent_id, '00000000-0000-0000-0000-000000000000')"), "sort_order"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index(
        "uq_categories_parent_slug",
        "categories",
        [sa.text("coalesce(parent_id, '00000000-0000-0000-0000-000000000000')"), sa.text("(slug->>'tr')")],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )


def downgrade() -> None:
    op.drop_index("uq_categories_parent_slug", table_name="categories")
    op.drop_index("uq_categories_parent_sort", table_name="categories")
