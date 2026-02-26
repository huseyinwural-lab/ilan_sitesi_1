# PUBLIC PHASE STRATEJİK PLAN (A+A)

## Amaç
Admin fazı kapandıktan sonra büyüme odağını kullanıcı tarafına taşıyarak arama→detay→iletişim dönüşümünü artırmak.

## Sprint Bazlı Plan

### Sprint P-UX-1 — Search Akış Optimizasyonu
- Suggest deneyimi: açılış gecikmesi, seçim davranışı, empty/loading state
- Sonuç listesi: ilk render ve filtre etkileşimi hız iyileştirmeleri
- Facet sadeleştirme: kullanılmayan facetlerin azaltılması, disabled logic netliği
- Çıkışlar:
  - Suggest → result geçiş oranında artış
  - Daha düşük ilk sonuç render süresi

### Sprint P-UX-2 — Listing Detail Conversion
- CTA hiyerarşisi netleştirme (contact/favorite/profile)
- Premium badge görünürlüğü ve güven sinyalleri
  - watermark görünürlüğü
  - güncelleme tarihi
  - doğrulama/seller güven bilgisi
- Mobil yerleşim optimizasyonu
- Çıkışlar:
  - result_click → detail_view artışı
  - detail_view → contact_click artışı

### Sprint P-UX-3 — Funnel Telemetry + Drop-off Yönetimi
- Event altyapısı + dashboard
- Adım bazlı drop-off ölçümü ve düzenli raporlama
- Çıkışlar:
  - Ölçülebilir funnel
  - Haftalık optimizasyon backlog’u

## Event Tracking (Implement Yaklaşımı A)

### Backend
- Endpoint: `POST /api/analytics/events`
- Tablo: `analytics_events`
  - `id`
  - `session_id`
  - `event_name`
  - `page`
  - `referrer`
  - `meta_json`
  - `created_at`
- Desteklenen eventler:
  - `suggest_open`
  - `search_submit`
  - `result_click`
  - `detail_view`
  - `contact_click`

### Frontend Emit Noktaları
- Header search suggest açılışı: `suggest_open`
- Search submit: `search_submit`
- Result card click: `result_click`
- Detail page load: `detail_view`
- Contact CTA click: `contact_click`

### Ölçüm KPI
- `suggest_open -> search_submit`
- `search_submit -> result_click`
- `result_click -> detail_view`
- `detail_view -> contact_click`
- Step drop-off yüzdesi

## Paralel P1 Hardening
- Suggest cache Redis’e taşıma planı
- Nightly DB ↔ Meili drift cron
- Admin health widget (index status)
