# MIGRATION_DRIFT_SIMULATION_EVIDENCE

**Tarih:** 2026-02-22 01:20:30 UTC

## Adım 1 — Current
```
alembic current
```
**Not:** Çoklu head mevcut.

## Adım 2 — Downgrade
```
alembic downgrade -1
```
**Not:** Çoklu head uyarısı alındı (beklenen).

## Adım 3 — Migration Gate (Preview Mode)
```
GET http://localhost:8001/api/health/db
```
Yanıt:
```
HTTP/1.1 503
{"migration_state":"migration_required", "reason":"migration_required"}
```

## Adım 4 — Upgrade
```
alembic upgrade heads
```
İlk deneme: `DuplicateTable: category_schema_versions` (downgrade rollback eksikliği)

**Düzeltme:**
```
DROP TABLE IF EXISTS category_schema_versions CASCADE;
```
Ardından `alembic upgrade heads` başarıyla tamamlandı.

## Adım 5 — Gate OK
```
GET http://localhost:8001/api/health/db
```
Yanıt:
```
HTTP/1.1 200
{"migration_state":"ok"}
```
