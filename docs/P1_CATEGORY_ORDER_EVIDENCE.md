# P1 Category Order Evidence

Date: 2026-02-25

## DB/Migration
- P55 migration reindex: tum parent cocuklari 1..N olarak normalize edildi.
- Unique index: parent_id + sort_order ve parent_id + slug(tr) (soft delete haric).

## UI
- Kategori duzenleme ekrani: sira alani read-only + 'Otomatik' badge.
- Vasita modul uyarisi + alt kategori kilidi.
- Screenshot: /app/screenshots/admin-categories-order-auto.png
