# P0 Vehicle Selector Stabilizasyonu — Kanıt Notu

Tarih: 2026-02-25

## Kapsam
- ListingWizard + VehicleSelector zincir state stabilizasyonu
- `year >= 2000` için trim zorunluluğu
- `year < 2000` için manuel trim zorunluluğu

## Uygulanan Düzeltmeler
- Frontend:
  - `Step4YearTrim.js`: Year→Make→Model→Options→Trim zinciri, downstream reset kuralları, async race guard (request id), manual trim UI/validasyon.
  - `Step2Brand.js`: make değişiminde model/year/trim/manual/filter state reset + payload temizliği.
  - `Step3Model.js`: model değişiminde year/trim/manual/filter state reset + payload temizliği.
  - `WizardContext.js`: merkezi wizard state’e `vehicle_trim_id`, `vehicle_trim_label`, `manual_trim_flag`, `manual_trim_text` ve trim filter alanları eklendi; category değişiminde vehicle state reset; publish payload güncellendi.
  - `Step4Review.js`: manual trim/trim label gösterimi güncellendi.
- Backend:
  - `server.py`:
    - `_validate_vehicle_selector_payload(...)` eklendi.
    - `_apply_listing_payload_sql(...)` içinde explicit null temizliği + make/model clear desteği + business rule validasyonu.

## Curl Doğrulama Sonuçları
- `GET /api/vehicle/years` → `200`
- `GET /api/vehicle/makes?year=...` → `200`
- `GET /api/vehicle/models?...` → `200`
- `GET /api/vehicle/options?...` → `200`
- `GET /api/vehicle/trims?...` → `200`

### İş kuralı doğrulaması
- `PATCH /api/v1/listings/vehicle/{id}/draft` (year>=2000, trim yok) → `422`  
  Mesaj: `year >= 2000 için vehicle_trim_id zorunludur`
- `PATCH /api/v1/listings/vehicle/{id}/draft` (year<2000, manual yok) → `422`  
  Mesaj: `year < 2000 için manual_trim_flag=true zorunludur`
- `PATCH /api/v1/listings/vehicle/{id}/draft` (year<2000, manual geçerli) → `200`
- `PATCH /api/v1/listings/vehicle/{id}/draft` (year>=2000, trim geçerli) → `200`

## Testing Agent Sonucu
Kaynak rapor: `/app/test_reports/iteration_12.json`

- Backend: Kritik issue yok, doğrulama senaryoları PASS
- Frontend: Zincir seçim ve kural senaryoları PASS
- Doğrulanan senaryolar:
  - Year değişimi downstream reset
  - Make değişimi downstream reset
  - Model sonrası trim yükleme
  - `year>=2000` trim zorunlu
  - `year<2000` manual trim zorunlu

## Not
- Test kapsamı için preview DB’ye `1995` legacy trim satırı seed edilmiştir (UI’de `<2000` manuel trim senaryosunu çalıştırmak için).