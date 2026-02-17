# Vehicle Listing Payload Contract v2 (Wizard v2 submit)

## Endpoint (öneri)
- POST `/api/v1/user-panel/vehicle-listings` (v2’de implement edilecek)

## Zorunlu alanlar
- `country` (string)
- `category_key` (string)  // segment slug
- `make_key` (string)
- `model_key` (string)
- `year` (int)
- `mileage_km` (int)
- `price_eur` (number)
- `condition` (string: new/used/damaged gibi)

## Opsiyonel alanlar
- `trim_key` (string|null)  // placeholder
- `fuel_type` (string|null) // electric burada gelir
- `transmission` (string|null)
- `body_type` (string|null)
- `drivetrain` (string|null)
- `power_hp` (int|null)
- `engine_cc` (int|null)

## Notlar
- Make/Model backend tarafında master data enforcement ile doğrulanır.
- Foto doğrulaması media policy’ye göre yapılır.
