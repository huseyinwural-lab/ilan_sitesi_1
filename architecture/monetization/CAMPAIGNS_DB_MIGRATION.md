# Campaigns DB Migration (V1)

## Table: campaigns

Columns:
- id (UUID, PK)
- type (individual|corporate)
- country_scope (global|country)
- country_code (nullable)
- name
- description (nullable)
- status (draft|active|paused|archived)
- start_at / end_at
- priority (low|medium|high)
- duration_days (individual)
- quota_count (corporate)
- price_amount
- currency_code (derived)
- created_by_admin_id (FK users.id)
- created_at / updated_at

Indexes:
- type
- status
- start_at
- end_at
- country_code
- priority

## Notes
- currency_code is derived from country_code (COUNTRY_CURRENCIES mapping)
- DB gate: endpoints return 503 DB_NOT_READY when DB not ready
