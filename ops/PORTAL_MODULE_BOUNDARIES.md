# PORTAL_MODULE_BOUNDARIES

## Amaç
Portal ayrımı “import boundary” ile desteklenerek yanlış portal kodunun yanlış bundle’a sızmasını engellemek.

## Dizin Yapısı
- `src/portals/public/*`
- `src/portals/dealer/*`
- `src/portals/backoffice/*`

## Ortak Paylaşılan Katman
- `src/shared/*`
  - `shared/ui-kit`
  - `shared/auth-client`
  - `shared/api-client`
  - `shared/types`

## Bağımlılık Kuralı
- Public bundle içinden **admin/dealer import’u yasak**.
- Dealer bundle içinden admin import’u yasak.
- Backoffice bundle içinden public/dealer import’u serbest (ama önerilen: shared üzerinden).

## Uygulama Disiplini
- `App.js` sadece:
  - public/individual route’larını statik import eder
  - dealer/backoffice portal app’lerini **lazy loader** ile import eder
- Admin layout + admin sayfalar sadece backoffice portal app içinde import edilir.
