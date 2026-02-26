"""
P57: Category P0 stabilization (module normalization + scoped order conflict fix)
"""
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p57_category_ordering_stabilization"
down_revision: Union[str, Sequence[str], None] = "p56_category_scope_ordering"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _scope_label(country_code, module, parent_id) -> str:
    country = country_code or "GLOBAL"
    parent = str(parent_id) if parent_id else "ROOT"
    return f"country={country} | module={module} | parent_id={parent}"


def _write_report(entries: list[dict], conflict_count: int, affected_ids: list[str]) -> None:
    report_path = Path(__file__).resolve().parents[3] / "docs" / "CATEGORY_ORDER_MIGRATION_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    uniq_ids = sorted(set(affected_ids))
    lines: list[str] = [
        "# CATEGORY ORDER MIGRATION REPORT",
        "",
        f"- Generated at: {datetime.now(timezone.utc).isoformat()}",
        f"- Çakışma sayısı: {conflict_count}",
        f"- Düzeltme yapılan kayıt sayısı: {len(uniq_ids)}",
        "",
        "## Düzeltme Yapılan ID’ler",
        "",
    ]

    if uniq_ids:
        for item_id in uniq_ids:
            lines.append(f"- {item_id}")
    else:
        lines.append("- Yok")

    lines.extend(["", "## Scope Bazlı Önce/Sonra Order Listesi", ""])
    if not entries:
        lines.append("- Çakışma tespit edilmedi.")
    else:
        for idx, entry in enumerate(entries, start=1):
            lines.extend([
                f"### {idx}) {entry['scope_label']}",
                f"- Scope çakışma adedi: {entry['conflict_count']}",
                "- Önce:",
            ])
            for row in entry["before"]:
                lines.append(f"  - {row}")
            lines.append("- Sonra:")
            for row in entry["after"]:
                lines.append(f"  - {row}")
            lines.append("- Düzeltme yapılan ID’ler:")
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
    if "categories" not in set(inspector.get_table_names()):
        return

    # 1) module normalization
    op.execute(
        """
        UPDATE categories
        SET module = CASE
            WHEN module IS NULL OR btrim(module) = '' THEN 'other'
            WHEN lower(btrim(module)) IN ('emlak', 'real_estate', 'realestate', 'real-estate') THEN 'real_estate'
            WHEN lower(btrim(module)) IN ('vasita', 'vehicle') THEN 'vehicle'
            WHEN lower(btrim(module)) = 'other' THEN 'other'
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
    total_conflict_count = 0

    for (country_code, module, parent_id), scope_rows in by_scope.items():
        before = [f"{row.id}: {int(row.sort_order or 0)}" for row in scope_rows]
        after: list[str] = []
        scope_affected_ids: list[str] = []
        scope_conflict_count = 0

        by_order = defaultdict(list)
        for row in scope_rows:
            old_order = int(row.sort_order or 0)
            if old_order > 0:
                by_order[old_order].append(row)

        assigned_orders: set[int] = {order for order, rows_with_order in by_order.items() if len(rows_with_order) == 1}
        reassignment_rows = []
        preserved_ids = set()

        for order, rows_with_order in sorted(by_order.items(), key=lambda item: item[0]):
            if len(rows_with_order) <= 1:
                preserved_ids.add(str(rows_with_order[0].id))
                continue
            keep_row = rows_with_order[0]
            preserved_ids.add(str(keep_row.id))
            assigned_orders.add(order)
            reassignment_rows.extend(rows_with_order[1:])

        for row in scope_rows:
            old_order = int(row.sort_order or 0)
            if old_order <= 0:
                reassignment_rows.append(row)

        next_candidate = 1
        reassigned_orders: dict[str, int] = {}
        for row in reassignment_rows:
            while next_candidate in assigned_orders:
                next_candidate += 1
            reassigned_orders[str(row.id)] = next_candidate
            assigned_orders.add(next_candidate)
            next_candidate += 1

        for row in scope_rows:
            old_order = int(row.sort_order or 0)
            row_id = str(row.id)

            if row_id in reassigned_orders:
                new_order = reassigned_orders[row_id]
                scope_conflict_count += 1
            else:
                new_order = old_order

            after.append(f"{row.id}: {new_order}")

            if old_order != new_order:
                bind.execute(
                    sa.text("UPDATE categories SET sort_order = :sort_order WHERE id = :id"),
                    {"sort_order": new_order, "id": row.id},
                )
                scope_affected_ids.append(str(row.id))
                affected_ids.append(str(row.id))

        if scope_conflict_count > 0:
            total_conflict_count += scope_conflict_count
            report_entries.append(
                {
                    "scope_label": _scope_label(country_code, module, parent_id),
                    "conflict_count": scope_conflict_count,
                    "before": before,
                    "after": after,
                    "affected_ids": scope_affected_ids,
                }
            )

    op.execute("DROP INDEX IF EXISTS uq_categories_scope_sort")
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

    _write_report(report_entries, total_conflict_count, affected_ids)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "categories" not in set(inspector.get_table_names()):
        return

    op.execute("DROP INDEX IF EXISTS uq_categories_scope_sort")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_parent_sort
        ON categories (coalesce(parent_id, '00000000-0000-0000-0000-000000000000'::uuid), sort_order)
        WHERE is_deleted = false
        """
    )