
# P19 Analytics Segmentation Spec (v1)

**Amaç:** Büyüme ve kullanım verilerini ülke bazlı analiz edebilmek.

## 1. Veri Yapısı (Growth Events)
`growth_events` tablosunda `country_code` alanı (P19.1 migration ile eklendi) kritik segmentasyon anahtarıdır.

### Event Zenginleştirme
*   **Source:** Request Header (`CF-IPCountry` veya `X-Country-Code`)
*   **Fallback:** User's `country_code`.
*   **Logic:** Event loglanırken `country_code` mutlaka doldurulmalıdır.

## 2. Dashboard Filtreleme
Admin paneli (`/admin/growth`) artık global değil, filtrelenebilir olmalıdır.
*   `GET /api/v1/admin/growth/overview?country=TR`
*   `GET /api/v1/admin/growth/overview?country=DE`

## 3. Metrikler (Segmented)
*   **Total Users:** `COUNT(users) WHERE country_code = X`
*   **New Users:** `COUNT(users) WHERE country_code = X AND created_at > Y`
*   **Sales:** `COUNT(growth_events) WHERE type='sale' AND country_code = X`
*   **Revenue:** `SUM(amount)` (Currency conversion gerekebilir).
