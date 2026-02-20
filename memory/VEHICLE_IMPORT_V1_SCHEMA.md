# VEHICLE_IMPORT_V1_SCHEMA

## JSON Yapısı
```json
{
  "makes": [
    {
      "name": "Ford",
      "slug": "ford",
      "country_code": "DE",
      "active": true
    }
  ],
  "models": [
    {
      "make_slug": "ford",
      "name": "Focus",
      "slug": "focus",
      "vehicle_type": "car",
      "active": true
    }
  ]
}
```

## Alanlar
### Make
- `name` (string, zorunlu)
- `slug` (string, zorunlu, lowercase + slug format)
- `country_code` (string, zorunlu, ISO-2)
- `active` (boolean, opsiyonel, default: true)

### Model
- `make_slug` (string, zorunlu)
- `name` (string, zorunlu)
- `slug` (string, zorunlu, lowercase + slug format)
- `vehicle_type` (string, zorunlu)
- `active` (boolean, opsiyonel, default: true)

## vehicle_type Enum
`car`, `suv`, `offroad`, `pickup`, `truck`, `bus`

## Validasyon Notları
- `make_slug` payload içinde olmalı ya da DB’de tekil olmalı.
- `vehicle_type` enum dışı ise kayıt **invalid** kabul edilir.
- `make_slug + model slug` kombinasyonu payload içinde tekrar edemez.
