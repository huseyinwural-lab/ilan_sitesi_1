# Vehicle Segment Required Fields Matrix v2

Elektrikli ayrı segment değildir.

## Ortak zorunlu alanlar (tüm segmentler)
- `year`
- `mileage_km`
- `price_eur`
- `condition`
- `fuel_type`
- `transmission`

## Segment bazlı ek zorunlular
### motosiklet
- `engine_cc` (zorunlu)
- `power_hp` (opsiyonel)

### ticari-arac
- `body_type` (zorunlu)

### arazi-suv-pickup
- `drivetrain` (opsiyonel; v2’de zorunlu değil)

## Not
Bu matris, UI-side validation + backend authoritative validation için tek kaynak olmalıdır.
