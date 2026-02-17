# MASTER_DATA_IMPORT_JOBS_SPEC (Standard)

## Kapsam
Master Data için import işlemleri tek bir standart üzerinden izlenebilir olmalıdır.

## Giriş
- Format: CSV/JSON upload
- Job modeli:
  - job_id
  - created_at
  - created_by
  - type (mdm_attributes / vehicle_makes / vehicle_models ...)
  - status (staged/validated/activated/rolled_back/failed)

## Validation
- Validation errors listesi:
  - row
  - field
  - code
  - message

## Rollback
- Activate sonrası rollback desteklenir.
- Rollback işlemi audit log’a yazılır.

## Audit Log
- Append-only JSONL
- Kim yaptı, ne zaman, hangi job

## UI Beklentileri
- Import jobs listesi
- Job detay ekranı
- Hata raporu indirme

> Not: Vehicle Master Data (file-based) için bu standart zaten kısmen uygulanmış durumda.
