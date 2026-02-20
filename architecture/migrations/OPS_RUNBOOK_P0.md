# OPS Runbook — Mongo Exit P0 (Auth + Applications)

## 1) Secret’lar
Preview + Prod:
- DATABASE_URL
- DB_POOL_SIZE (default: 5)
- DB_MAX_OVERFLOW (default: 5)
- DB_SSL_MODE (prod için require)
- APP_ENV (dev|preview|prod)

## 2) Deploy / Restart
- Secret’lar girildikten sonra **hard restart** (deploy/restart) yapılmalı.

## 3) Healthcheck
- GET /api/health → 200
- GET /api/health/db → 200 (DB bağlı) / 503 degraded (DB yok)

## 4) Migration
- Komut: `alembic upgrade head`
- Not: P0 migration seti **auth + applications** tablolarını içerir.

## 5) Seed (Preview only)
- Komut: `python /app/backend/scripts/seed_applications_preview.py`
- Sonuç: 5 bireysel + 5 kurumsal demo başvuru

## 6) Cutover (Session Invalidate)
- Refresh token tablosu sıfırlanır veya tüm token’lar revoked edilir.

## 7) Rollback
- DB migration rollback gerekiyorsa: `alembic downgrade -1`
- APP_ENV prod ise fail-fast geri devreye girer.
