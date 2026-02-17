# ADMIN_DEALER_MODULE_COMPLETE

## Sprint
SPRINT 1.1 — Dealer Management

## Amaç
Admin panelde dealer yönetimini gerçek veri ile çalışır hale getirmek.

## Backend
### Endpoints
- `GET /api/admin/dealers`
  - country filtre: admin country context `?country=XX`
  - pagination: `skip`, `limit`
  - filtreler: `status` (dealer_status), `search` (email regex)
- `GET /api/admin/dealers/{dealer_id}`
  - dealer detail + paket bağlantısı (plan_id + last_invoice)
- `POST /api/admin/dealers/{dealer_id}/status`
  - body: `{ dealer_status: "active" | "suspended" }`
  - audit-first zorunlu

### Data model
- Dealer: `users` koleksiyonunda `role="dealer"` + `dealer_status`

### Country-scope enforcement
- `?country=XX` country mode’da dealer `country_code` ile filtrelenir.

## Audit
- Event: `DEALER_STATUS_CHANGE`
- Alanlar: previous_status → new_status, admin_user_id, dealer_id (resource_id), applied

## Frontend (Backoffice)
- Route: `/admin/dealers` (Layout altında)
- Liste: email/country/status + suspend/activate aksiyonu

## Kabul Kriteri
- Dealer list country filtreli çalışır
- Dealer status değişimi audit yazmadan commit olmaz
- Status değişimi sonrası UI liste güncellenir

## Notlar
- Dealer detail UI (ayrı sayfa) Sprint 1.1’de backend hazır; UI detay ekranı Sprint 1.1.5’te genişletilebilir.
