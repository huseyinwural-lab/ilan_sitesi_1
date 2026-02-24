# MONGO_SQL_MIGRATION_EVIDENCE

**Son güncelleme:** 2026-02-23 23:44:57 UTC

## Status
- P0 admin chain (system_settings + admin_invites) SQL'e taşındı (runtime).
- Mongo kaynak DB preview ortamında kapalı (app.state.db=None) olduğu için veri dump alınmadı.

## Kontroller
- P0 admin chain curl:
  - GET /api/admin/system-settings → 200 (SQL)
  - GET /api/admin/invite/preview?token=invalid → 404 (SQL)
- Master Data curl:
  - GET /api/admin/attributes → 200 (SQL)
  - GET /api/admin/vehicle-makes → 200 (SQL)
  - GET /api/admin/menu-items → 200 (SQL)
- Finance/Config curl:
  - GET /api/admin/tax-rates → 200 (SQL)
  - GET /api/admin/reports → 200 (SQL)
- Admin UI:
  - `/app/screenshots/system-settings-sql.png`
  - `/app/screenshots/vehicle-makes-sql.png`
  - `/app/screenshots/tax-rates-sql.png`
- SQL tablo sayımları (admin_invites, system_settings): preview'da boş (0).
- Mongo kaynak DB preview ortamında kapalı (app.state.db=None) olduğu için dump/checksum alınmadı.