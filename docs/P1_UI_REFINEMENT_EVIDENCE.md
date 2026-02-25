# P1 UI Refinement Evidence

Date: 2026-02-25

## Tema Yönetimi
- Admin UI ekran görüntüsü: `/app/screenshots/admin-theme-management.png`
- API doğrulamaları:
  - `GET /api/admin/site/theme` → 200 OK
  - `PUT /api/admin/site/theme/config` → 200 OK (draft kaydı)
  - `POST /api/admin/site/theme/config/{id}/publish` → 200 OK (WCAG AA raporu döndü)
- Örnek publish yanıtı (kısaltılmış): `validation_report` tüm kalemlerde **pass: true**

## Header CTA (İlan Ver)
- Authenticated durumda CTA görünür: `/app/screenshots/header-cta.png`
- CTA route: `/ilan-ver/kategori-secimi`

## Kampanyalar Menü Temizliği
- Admin sidebar’dan eski “Kampanyalar” (bireysel/kurumsal) kaldırıldı.
- `/admin/individual-campaigns` ve `/admin/corporate-campaigns` route’ları devre dışı.

## Reklam Soft Delete
- DELETE çağrısı:
  - `DELETE /api/admin/ads/b59629c8-0a2e-4a79-b303-2cb650931975` → `{ "ok": true }`
- Doğrulama:
  - `GET /api/admin/ads` sonucunda silinen ID listede görünmüyor.
- Audit log: `AD_DELETED` aksiyonu yazıldı.
