# Vehicle Mileage/Year Sanity Rules v1

## Amaç
Fraud sinyali üretmek; MVP’de hard-block yapmak değil.

## Kural
- `mileage_km / age_years` çok yüksekse → warning
- Örnek heuristic:
  - yaş = current_year - year
  - yaş <= 0 ise warning (future year)
  - yaş > 0 ve `mileage_km / yaş > 60000` → warning

## Davranış
- UI: uyarı banner’ı
- Backend: log/audit (fraud signal)

> Not: v3.5’te trust layer hard-block’a taşınabilir.
