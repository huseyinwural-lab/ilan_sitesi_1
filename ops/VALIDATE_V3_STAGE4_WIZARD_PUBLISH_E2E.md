# Stage‑4 Wizard Publish — E2E Scenarios

## 1) Başarılı publish
- segment=otomobil
- valid make/model
- year/km/price/fuel/transmission/condition dolu
- 3 foto (>=800x600)
- submit → published
- detail sayfasında 3 foto görünüyor

## 2) Invalid make/model
- make_key master data’da yok → 422
- model_key make altında yok → 422

## 3) 2 foto
- submit → 422 (MIN_PHOTOS)

## 4) inactive model
- submit → 422

## 5) segment required field missing
- ör: mileage_km missing → 422

## 6) draft media public değil
- publish olmadan /media/listings/... erişimi 404/403
