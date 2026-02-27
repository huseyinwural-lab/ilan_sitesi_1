# P1_DEALER_CONSULTANT_TRACKING_ALIGNMENT_EVIDENCE

Tarih: 2026-02-27

## Kapsam
- Sıralama korunarak sonraki adım tamamlandı: **Danışman Takibi**
- Gerekli iyileştirmelerle birlikte **Favoriler/Raporlar** entegrasyonu stabilize edildi.

## Danışman Takibi

### Backend
- Yeni endpoint: `GET /api/dealer/consultant-tracking`
- Parametre: `sort_by` (`rating_desc`, `message_change_desc`, `messages_desc`, `name_asc`)
- Dönüş:
  - `consultants`
    - `consultant_id`, `full_name`, `email`, `role`, `is_active`
    - `active_listing_count`, `listing_count`
    - `message_count`, `message_count_7d`, `message_change_7d`, `message_change_label`
    - `service_score`, `review_count`, `detail_route`
  - `evaluations`
    - `evaluation_id`, `consultant_id`, `consultant_name`, `username`, `evaluation_date`, `score`, `comment`
  - `summary`

### Frontend (`/dealer/consultant-tracking`)
- Tablar:
  - `Danışmanlar`
  - `Danışman Hizmet Değerlendirmeleri`
- Filtreler:
  - arama
  - gelişmiş sıralama
- Danışman kartları + değerlendirme tablosu

## Stabilizasyon Notları
- Row2 sıra korunuyor, `Sanal Turlar` menüde yok.
- Favoriler ve Raporlar endpoint/UI entegrasyonu testlerle doğrulandı.
- Mesaj okunma akışı (`Okundu İşaretle`) regresyonsuz.

## Test Kanıtı
- Testing agent: `/app/test_reports/iteration_38.json` (backend/frontend PASS)
- Pytest birleşik set:
  - `test_dealer_consultant_tracking.py`
  - `test_dealer_favorites_reports_v2.py`
  - `test_dealer_messages_customers.py`
  - Sonuç: `71 passed`

**MOCKED API YOK**
