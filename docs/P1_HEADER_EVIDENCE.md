# P1 Header Evidence

## Migration Gate
- `python3 /app/scripts/migration_dry_run.py` → PASS (2026-02-25)
- `alembic upgrade heads` → OK (p52_site_header_config)
- `/api/health/db` → ok

## API Curl Kanıtı
### Admin Header GET
```bash
curl -X GET "$API/admin/site/header" -H "Authorization: Bearer $ADMIN"
```
Response (örnek):
```json
{"id":"...","logo_url":"/api/site/assets/header/02adf947-...png?v=1","version":1}
```

### Logo Upload
```bash
curl -X POST "$API/admin/site/header/logo" -H "Authorization: Bearer $ADMIN"   -F "file=@/tmp/header-logo.png"
```
Response (örnek):
```json
{"ok":true,"logo_url":"/api/site/assets/header/02adf947-...png?v=1","version":1}
```

### Public Header GET (cacheable)
```bash
curl -X GET "$API/site/header"
```
Response (örnek):
```json
{"logo_url":"/api/site/assets/header/02adf947-...png?v=1","version":1}
```

## UI Screenshot Kanıtı
- `test1-guest-header.png` (Guest header)
- `test2-auth-header.png` (Auth header)
- `test3-admin-header-management.png` (Admin Header Yönetimi)

## Test Notları
- Guest/Auth header aksiyonları doğrulandı.
- Cache invalidation için logo_url versiyon parametresi kullanıldı.
