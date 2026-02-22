# PREVIEW_ACTIVATION_RUNBOOK

**Tarih:** 2026-02-22 00:54:38 UTC

## 1) Secret Check
- `DATABASE_URL_PREVIEW` secret injection (sslmode=require, localhost yok)
- Runtime doğrulama: `printenv | rg DATABASE_URL`

## 2) Health Gate
- `GET /api/health/db` → 200 + db_status=ok
- `migration_state`:
  - Head değil → 503 + migration_required
  - Head → 200 + ok

## 3) Migration Parity
- `alembic current`
- `alembic upgrade head`
- `\d dealer_profiles` → `gdpr_deleted_at` kolonu

## 4) Auth Login
- Consumer: /login
- Dealer: /dealer/login
- Admin: /admin/login

## 5) GDPR Export
- `/api/v1/users/me/data-export` → JSON + in-app notification

## 6) Soft Delete
- `/api/v1/users/me/account` → gdpr_deleted_at + 30 gün

## 7) Dealer Panel
- `/dealer` ana sayfa yükleniyor

## 8) Admin Panel
- `/admin` ana sayfa yükleniyor
