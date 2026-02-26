"""
P56: Category module normalization + scoped order uniqueness
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p56_category_scope_ordering"
down_revision: Union[str, Sequence[str], None] = "p55_category_ordering"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _scope_label(country_code, module, parent_id) -> str:
    country = country_code or "GLOBAL"
    parent = str(parent_id) if parent_id else "ROOT"
    return f"country={country} | module={module} | parent_id={parent}"


def _write_report(entries: list[dict], total_conflicting_rows: int, affected_ids: list[str]) -> None:
    report_path = Path(__file__).resolve().parents[3] / "docs" / "CATEGORY_ORDER_MIGRATION_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    unique_ids = sorted(set(affected_ids))
    lines: list[str] = [
        "# CATEGORY ORDER MIGRATION REPORT",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Scope bazlı düzeltme yapılan kayıt grubu: {len(entries)}",
        f"- Çakışma sayısı (kayıt bazlı): {total_conflicting_rows}",
        f"- Etkilenen kayıt sayısı: {len(unique_ids)}",
        "",
        "## Etkilenen Kayıt ID'leri",
        "",
    ]

    if unique_ids:
        for item_id in unique_ids:
            lines.append(f"- {item_id}")
    else:
        lines.append("- Yok")

    lines.extend(["", "## Scope Bazlı Düzeltme Detayları", ""])
    if not entries:
        lines.append("- Çakışma tespit edilmedi.")
    else:
        for index, entry in enumerate(entries, start=1):
            lines.extend([
                f"### {index}) {entry['scope_label']}",
                f"- Çakışan kayıt adedi: {entry['conflicting_rows']}",
                "- Öncesi order_index listesi:",
            ])
            for row in entry["before"]:
                lines.append(f"  - {row}")
            lines.append("- Sonrası order_index listesi:")
            for row in entry["after"]:
                lines.append(f"  - {row}")
            lines.append("- Bu scope için etkilenen kayıt ID'leri:")
            if entry["affected_ids"]:
                for item_id in entry["affected_ids"]:
                    lines.append(f"  - {item_id}")
            else:
                lines.append("  - Yok")
            lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "categories" not in tables:
        return

    op.execute(
        """
        UPDATE categories
        SET module = CASE
            WHEN module IS NULL OR btrim(module) = '' THEN 'vehicle'
            WHEN lower(btrim(module)) IN ('vehicle', 'vasita') THEN 'vehicle'
            WHEN lower(btrim(module)) IN ('real_estate', 'realestate', 'real-estate', 'emlak') THEN 'real_estate'
            WHEN lower(btrim(module)) IN ('other', 'machinery', 'services', 'jobs') THEN 'other'
            ELSE 'other'
        END
        """
    )

    rows = bind.execute(
        sa.text(
            """
            SELECT id, country_code, module, parent_id, sort_order, created_at
            FROM categories
            WHERE is_deleted = false
            ORDER BY
                coalesce(country_code, '') ASC,
                module ASC,
                parent_id NULLS FIRST,
                sort_order ASC NULLS LAST,
                created_at ASC NULLS LAST,
                id ASC
            """
        )
    ).fetchall()

    by_scope = defaultdict(list)
    for row in rows:
        by_scope[(row.country_code, row.module, row.parent_id)].append(row)

    report_entries: list[dict] = []
    affected_ids: list[str] = []
    total_conflicting_rows = 0

    for (country_code, module, parent_id), scope_rows in by_scope.items():
        order_counter = defaultdict(int)
        invalid_rows = 0
        for row in scope_rows:
            current_order = int(row.sort_order or 0)
            if current_order <= 0:
                invalid_rows += 1
                continue
            order_counter[current_order] += 1

        duplicate_rows = sum(count for count in order_counter.values() if count > 1)
        conflicting_rows = invalid_rows + duplicate_rows
        if conflicting_rows == 0:
            continue

        total_conflicting_rows += conflicting_rows
        before_orders = [f"{row.id}: {int(row.sort_order or 0)}" for row in scope_rows]
        after_orders: list[str] = []
        scope_affected_ids: list[str] = []

        for idx, row in enumerate(scope_rows, start=1):
            old_order = int(row.sort_order or 0)
            new_order = idx
            after_orders.append(f"{row.id}: {new_order}")
            if old_order != new_order:
                bind.execute(
                    sa.text("UPDATE categories SET sort_order = :sort_order WHERE id = :id"),
                    {"sort_order": new_order, "id": row.id},
                )
                scope_affected_ids.append(str(row.id))
                affected_ids.append(str(row.id))

        report_entries.append(
            {
                "scope_label": _scope_label(country_code, module, parent_id),
                "conflicting_rows": conflicting_rows,
                "before": before_orders,
                "after": after_orders,
                "affected_ids": scope_affected_ids,
            }
        )

    op.execute("DROP INDEX IF EXISTS uq_categories_parent_sort")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_scope_sort
        ON categories (
            coalesce(country_code, '__GLOBAL__'),
            module,
            coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid),
            sort_order
        )
        WHERE is_deleted = false
        """
    )

    _write_report(report_entries, total_conflicting_rows, affected_ids)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "categories" not in tables:
        return

    op.execute("DROP INDEX IF EXISTS uq_categories_scope_sort")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_parent_sort
        ON categories (coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid), sort_order)
        WHERE is_deleted = false
        """
    )