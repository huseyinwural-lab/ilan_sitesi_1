# HEALTH_OPS_VISIBILITY_SPEC

## Amaç
Ops dashboard için health görünürlüğünü artırmak.

## /api/health Alanları
- `config_state`: missing_database_url | ok
- `last_migration_check_at`: ISO timestamp
- `ops_attention`: true/false
- `last_db_error`: maskeli hata mesajı (max 500 karakter)

## Kurallar
- config missing → ops_attention=true
- migration_required → ops_attention=true
- healthy → ops_attention=false
- last_db_error yalnız hata durumunda set edilir

## Örnek
```
{
  "status": "healthy",
  "db_status": "ok",
  "config_state": "ok",
  "last_migration_check_at": "2026-02-22T01:08:17.950702+00:00",
  "ops_attention": false,
  "last_db_error": null
}
```
