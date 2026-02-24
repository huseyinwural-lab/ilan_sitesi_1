# Listing Quick Preview Modal Spec (UH1-E1)

**Amaç:** Snapshot listesinden hızlı önizleme sağlamak.

## Kapsam (Minimal v1)
- Kapak görseli
- Fiyat
- Status badge
- Görüntülenme sayısı
- Favori sayısı
- “İlana Git” butonu

## Veri Kaynağı
- `/api/v1/listings/my` response genişletilecek:
  - `view_count`
  - `favorite_count`
- Ek endpoint çağrısı yapılmayacak.

## Performans Kriteri
- Modal açılışı ek network çağrısı üretmeyecek.
- Snapshot listesinde gelen veri kullanılacak.
