"""
P32: enforce category_id on listings
"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa

revision: str = 'p32_listing_category_required'
down_revision: Union[str, Sequence[str], None] = 'p31_listing_contact_options'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT id FROM categories
        WHERE module = 'vehicle' AND (is_deleted IS NULL OR is_deleted = false)
        ORDER BY created_at ASC
        LIMIT 1
    """))
    row = result.fetchone()
    category_id = row[0] if row else None

    if category_id is None:
        category_id = uuid.uuid4()
        conn.execute(
            sa.text("""
                INSERT INTO categories (
                    id, parent_id, path, depth, sort_order, module, country_code, slug,
                    is_enabled, is_visible_on_home, is_deleted, inherit_enabled, inherit_countries,
                    allowed_countries, hierarchy_complete, listing_count, created_at, updated_at
                ) VALUES (
                    :id, NULL, '', 0, 0, 'vehicle', NULL, :slug,
                    true, false, false, true, true,
                    '[]', true, 0, now(), now()
                )
            """),
            {
                "id": str(category_id),
                "slug": '{"tr":"uncategorized","de":"uncategorized","fr":"uncategorized","en":"uncategorized"}',
            },
        )

    conn.execute(
        sa.text("UPDATE listings SET category_id = :category_id WHERE category_id IS NULL"),
        {"category_id": str(category_id)},
    )

    op.alter_column('listings', 'category_id', nullable=False)


def downgrade() -> None:
    op.alter_column('listings', 'category_id', nullable=True)
