# Listing Snapshot Spec (UH1.3)

## Blok
**Başlık:** Son İlanlarım

## Veri
- Son 5 ilan: `/api/v1/listings/my?limit=5`
- Alanlar: `title`, `status`, `moderation_reason`

## Status Badge
- `draft` → Taslak
- `pending_moderation` → Beklemede
- `published` → Onaylandı
- `rejected` / `needs_revision` → Reddedildi

## Moderation Reason Tooltip
- Kaynak: Listing payload içindeki `moderation_reason`.
- Boşsa: `N/A` göster.

## Aksiyon
- Hızlı Düzenle butonu (edit wizard).
