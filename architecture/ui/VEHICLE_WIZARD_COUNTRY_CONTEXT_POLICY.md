# Vehicle Wizard — Country Context Policy (v1)

## 1) Kaynaklar
- Country context şu öncelik sırası ile belirlenir:
  1) URL parametresi varsa (ör: `/:country/...`)
  2) CountryContext `selectedCountry`
  3) Default: `DE`

## 2) Master data
- Master data globaldir.
- Public API çağrılarında `country` parametresi v1’de:
  - cache key
  - future override hook

## 3) Listing payload
- Wizard submit payload içinde `country` zorunludur.
