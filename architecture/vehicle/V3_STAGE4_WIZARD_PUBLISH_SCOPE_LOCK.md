# FAZ‑V3 / Aşama 4 — Wizard Publish Scope Lock (Real Listing + Guard + Media)

## 1) Amaç
Wizard v2’den gelen payload ile **gerçek vasıta ilanı** üretmek:
- draft create
- media upload + register
- submit/publish attempt

## 2) Kapsam (LOCKED)
- Wizard payload → gerçek listing create/submit
- Publish Guard (hard‑block):
  - make/model master data enforcement
  - segment required field enforcement
  - min 3 foto + min 800x600
  - country zorunlu
- Media storage binding: **Local filesystem (v1)**
  - path: `/data/listing_media/{country}/{listing_id}/...`
  - public URL: `/media/listings/{listing_id}/{file}` (published only)

## 3) Hariç (Out of Scope)
- Trim/spec auto‑fill (V3.5)
- VIN doğrulama (V4)
- Provider tabanlı teknik spec doğrulama

## 4) Acceptance hedefi
- Wizard “Publish” gerçek endpoint’e bağlı
- Successful publish → detail sayfası + foto görünüyor
- 422 validation_errors UI’da listeleniyor
