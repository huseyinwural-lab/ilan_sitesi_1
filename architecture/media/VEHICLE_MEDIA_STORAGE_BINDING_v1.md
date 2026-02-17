# Vehicle Media Storage Binding v1

## Storage Backend = Local FS (LOCKED)
Bu sprintte medya storage v1 **local filesystem** üzerindedir.

## Path standardı (LOCKED)
- Base dir: `/data/listing_media`
- Layout:
  - `/data/listing_media/{country}/{listing_id}/<file>`

## Public URL standardı (LOCKED)
- Backend serve eder:
  - `GET /media/listings/{listing_id}/{file}`

## Access policy (LOCKED)
- Draft ilan medyası public olmaz.
- Published ilan medyası public olur.

## Upload stratejisi (v1)
- v1’de upload backend’e gelir (multipart)
- v2’de signed URL direct upload’a evrilebilir.

## Content validation
- content-type: `image/*`
- min resolution: 800x600
- path traversal koruması: safe join + allowlist
