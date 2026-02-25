# P1 Vehicle Selector Evidence

Date: 2026-02-25

## API curl
- `GET /api/vehicle/years` → 200
- `GET /api/vehicle/makes?year=2022` → 200
- `GET /api/vehicle/models?year=2022&make=audi` → 200
- `GET /api/vehicle/options?year=2022&make=audi&model=a4` → 200
- `GET /api/vehicle/trims?year=2022&make=audi&model=a4` → 200

## UI
- Araç seçim ekranı: `/app/screenshots/vehicle-selector.png`
- Trim zorunluluğu: yıl >= 2000 için trim seçimi required (UI disabled state)
