# VEHICLE_SLUG_NORMALIZATION_RULES

## Slug Üretim Kuralı (v1)
1. Unicode normalize (NFKD) + ASCII temizleme
2. Lowercase
3. Harf/rakam dışı karakterler `-` ile değiştirilir
4. Çoklu `-` tek `-` yapılır
5. Baştaki/sondaki `-` temizlenir

## Unique Key
- `make_slug + model_slug` kombinasyonu benzersiz olmalıdır.
- Duplicate slug varsa rapora yazılır ve **sonraki kayıtlar atlanır**.
