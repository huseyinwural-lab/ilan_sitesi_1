# P2 UI Teknik Borç + Legacy Publish Temizlik Raporu

## 1) UI Teknik Borç (Hydration Warning) Temizliği

Kapsam:
- `frontend/src/layouts/DealerLayout.js`
- `frontend/src/pages/admin/AdminCategories.js` (Visual Editor etkisi olan filtre alanları)

Yapılanlar:
- DealerLayout üst satır mağaza filtresi `<select>/<option>` yapısından menü tabanlı buton/dropdown yapısına taşındı.
- AdminCategories liste filtreleri (`module/status/image_presence`) `<select>` yerine buton-grup filtre yapısına taşındı.

Doğrulama:
- Smoke: `/tmp/p2-hydration-cleanup-smoke.png`
- Console log: `/root/.emergent/automation_output/20260227_170136/console_20260227_170136.log`
- Sonuç: `span/option/tr/tbody` hydration warning gözlenmedi.

## 2) Legacy Publish Fiziksel Temizlik

Kaldırılan route'lar:
- `POST /api/admin/ui/configs/{config_type}/publish/{config_id}`
- `GET /api/admin/ui/configs/{config_type}/legacy-usage`

Backward compatibility notu:
- Eski endpointler artık sistemde yoktur (`404 Not Found`).
- Geçerli publish kontratı:
  - `POST /api/admin/ui/configs/{config_type}/publish`

Doğrulama:
- Legacy publish route çağrısı: `404`
- Legacy usage route çağrısı: `404`
