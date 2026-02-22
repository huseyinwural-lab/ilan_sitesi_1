# SPRINT1_PREVIEW_E2E_EVIDENCE

**Tarih:** 2026-02-22
**Durum:** BLOCKED (Preview DB erişimi yok)

## API E2E (Beklenen)
- `GET /api/v1/users/me/profile` → 200
- `GET /api/v1/users/me/dealer-profile` → 200
- `GET /api/v1/users/me/data-export` → JSON + gdpr_export_completed + notification
- `DELETE /api/v1/users/me/account` → soft delete (30 gün)

## Honeypot
- company_website dolu → 400 + audit event: `register_honeypot_hit`

## Bildirim
- Export sonrası notification (severity=warning) UI’da görünür.

## Not
DB erişimi açıldığında gerçek curl çıktıları eklenecek.
