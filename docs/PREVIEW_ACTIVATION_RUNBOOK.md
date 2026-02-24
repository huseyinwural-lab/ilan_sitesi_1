# PREVIEW_ACTIVATION_RUNBOOK

**Tarih:** 2026-02-24 12:01:16 UTC

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

## 9) 520-scan Gate (Release zorunlu)
- **Release öncesi zorunlu adım.** 520=0 olmadan deploy yapılmaz.
- Komut seti (curl):
  - `curl {BASE}/api/health`
  - `curl {BASE}/api/health/db`
  - `curl -X POST {BASE}/api/auth/login`
  - `curl {BASE}/api/auth/me`
  - `curl {BASE}/api/v1/users/me/profile`
  - `curl {BASE}/api/v1/users/me/dealer-profile`
  - `curl {BASE}/api/v1/listings/my`
  - `curl {BASE}/api/admin/system-settings`
  - `curl {BASE}/api/admin/invite/preview`
  - `curl {BASE}/api/admin/listings`
  - `curl {BASE}/api/admin/users`
  - `curl {BASE}/api/admin/moderation/queue`
  - `curl {BASE}/api/admin/moderation/queue/count`
  - `curl {BASE}/api/v2/vehicle/makes?country=DE`
  - `curl {BASE}/api/v2/vehicle/models?make_key=<make_key>`
- Beklenen: 200/401/403/422 (422 sadece invite token eksikliği); **520=0**
