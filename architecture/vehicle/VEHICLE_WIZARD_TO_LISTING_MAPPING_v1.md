# Wizard → Listing Mapping v1 (FE → BE)

## Segment
- Wizard step1 segment seçimi → `category_key`

## Vehicle block
- Wizard step2
  - `make_key` → `vehicle.make_key`
  - `model_key` → `vehicle.model_key`
  - `year` → `vehicle.year`

## Attributes
- `mileage_km`
- `price_eur`
- `fuel_type` (electric burada)
- `transmission`
- `condition`

## Media
- Wizard step3 upload → `/api/v1/listings/vehicle/{id}/media`
- Backend response’daki `preview_url` wizard preview’de kullanılır

## Publish
- Wizard step4 publish → `/api/v1/listings/vehicle/{id}/submit`
- Başarılı → `detail_url` route’una yönlen
- 422 → `validation_errors[]` UI’da listelenir
