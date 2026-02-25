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

    op.execute("CREATE UNIQUE INDEX uq_categories_parent_sort ON categories (coalesce(parent_id, '00000000-0000-0000-0000-000000000000'), sort_order) WHERE is_deleted = false")
    op.execute("CREATE UNIQUE INDEX uq_categories_parent_slug ON categories (coalesce(parent_id, '00000000-0000-0000-0000-000000000000'), (slug->>'tr')) WHERE is_deleted = false")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_categories_parent_slug")
    op.execute("DROP INDEX IF EXISTS uq_categories_parent_sort")
