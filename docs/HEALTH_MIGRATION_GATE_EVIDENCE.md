# HEALTH_MIGRATION_GATE_EVIDENCE

**Tarih:** 2026-02-22
**Durum:** BLOCKED (Preview DB secret injection bekleniyor)

## Beklenen Kanıtlar
### Head eşit → OK
```
GET /api/health/db
```
Beklenen:
- HTTP 200
- `migration_state=ok`

### Head değil → Gate
```
GET /api/health/db
```
Beklenen:
- Preview/Prod: HTTP 503
- `migration_state=migration_required`

## Not
DB erişimi açıldığında gerçek çıktılar eklenecek.
