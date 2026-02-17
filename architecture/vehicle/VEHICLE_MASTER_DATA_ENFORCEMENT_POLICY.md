# Vehicle Master Data Enforcement Policy (Publish Guard v1)

## Amaç
Wizard publish sırasında make/model seçimlerinin master data ile uyumlu olduğunu garanti eder.

## Kurallar (LOCKED)
1) `make_key` master data makes içinde yoksa → **reject**
2) `model_key` ilgili make altında yoksa → **reject**
3) `is_active=false` olan make/model seçilemez → **reject**

## Uygulama noktası
- Backend publish endpoint’inde authoritative validation
- UI tarafında ek olarak seçim listeleri zaten master’dan geldiği için önleyici UX

## Country parametresi
- v1’de country sadece cache key / future hook.
