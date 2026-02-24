# Listing Quick Preview Actions Addendum

## Scope (P1)
- **Düzenle** (Edit)
- **Yayından Kaldır** (Unpublish) — sadece `approved/published` ilanlar

## Guard Kuralları
- Ownership: sadece ilan sahibi görebilir.
- Status guard: Unpublish yalnızca `published` statüsünde görünür.

## Confirmation Modal
- Unpublish için onay modalı zorunlu.
- Soft-delete yok; `status -> draft` dönüşümü **değil**. Endpoint `unpublish` ile statü `unpublished` olur.

## API
- `POST /api/v1/listings/vehicle/{listing_id}/unpublish`

## Audit
- Unpublish işlemi audit log üretmeli (event: `LISTING_UNPUBLISH`).
