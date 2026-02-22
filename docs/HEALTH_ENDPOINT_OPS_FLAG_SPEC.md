# HEALTH_ENDPOINT_OPS_FLAG_SPEC

## Amaç
Ops dashboard görünürlüğü için /api/health yanıtında ops_attention alanı.

## Alan
- `ops_attention` (boolean)
  - **true**: config missing veya migration_required (veya DB erişim sorunu)
  - **false**: healthy

## /api/health Örneği
```
{
  "status": "healthy",
  "db_status": "ok",
  "config_state": "ok",
  "last_migration_check_at": "2026-02-22T00:54:38Z",
  "ops_attention": false
}
```
