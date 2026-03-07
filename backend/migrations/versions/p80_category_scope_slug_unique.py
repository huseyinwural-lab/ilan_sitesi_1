"""Category scope slug unique index with dedup guard.

Revision ID: p80_category_scope_slug_unique
Revises: p79_rev_redirect_events
Create Date: 2026-03-07
"""

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "p80_category_scope_slug_unique"
down_revision: str | None = "p79_rev_redirect_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_categories_parent_slug")

    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                row_number() OVER (
                    PARTITION BY
                        coalesce(country_code, '__GLOBAL__'),
                        module,
                        coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid),
                        lower(coalesce(slug->>'tr', ''))
                    ORDER BY
                        created_at ASC NULLS LAST,
                        id ASC
                ) AS rn
            FROM categories
            WHERE is_deleted = false
        )
        UPDATE categories c
        SET
            is_deleted = true,
            is_enabled = false,
            deleted_at = COALESCE(c.deleted_at, now()),
            updated_at = now()
        FROM ranked r
        WHERE c.id = r.id
          AND r.rn > 1
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_scope_slug
        ON categories (
            coalesce(country_code, '__GLOBAL__'),
            module,
            coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid),
            lower(coalesce(slug->>'tr', ''))
        )
        WHERE is_deleted = false
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_categories_scope_slug")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_parent_slug
        ON categories (
            coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid),
            lower(coalesce(slug->>'tr', ''))
        )
        WHERE is_deleted = false
        """
    )
