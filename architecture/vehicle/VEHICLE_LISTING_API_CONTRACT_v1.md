# Vehicle Listing API Contract v1 (Stage‑4)

Base: `/api/v1`

## 1) Draft create
### POST `/listings/vehicle`
Create a draft vehicle listing.

Request (min):
```json
{
  "country": "DE",
  "category_key": "otomobil",
  "make_key": "bmw",
  "model_key": "3-serie",
  "year": 2020,
  "mileage_km": 85000,
  "price_eur": 15000,
  "fuel_type": "electric",
  "transmission": "automatic",
  "condition": "used"
}
```

Response 200:
```json
{
  "id": "<uuid>",
  "status": "draft",
  "validation_errors": [],
  "next_actions": ["upload_media", "submit"]
}
```

## 2) Media upload + register
### POST `/listings/vehicle/{id}/media`
Upload one or more images and register them to the draft listing.

Input: `multipart/form-data`
- `files`: one or multiple image files
- (optional) `cover_media_id`: string

Response 200:
```json
{
  "id": "<listing_id>",
  "status": "draft",
  "media": [
    {
      "media_id": "<uuid>",
      "file": "<stored_filename>",
      "width": 1200,
      "height": 800,
      "is_cover": true,
      "preview_url": "/api/v1/listings/vehicle/<id>/media/<media_id>/preview"
    }
  ]
}
```

## 3) Submit / Publish attempt
### POST `/listings/vehicle/{id}/submit`
Runs publish guard checks and changes status to `published` if ok.

Response 200 (success):
```json
{
  "id": "<uuid>",
  "status": "published",
  "validation_errors": [],
  "next_actions": ["view_detail"],
  "detail_url": "/ilan/vasita/<id>-<slug>"
}
```

Response 422 (guard fail):
```json
{
  "id": "<uuid>",
  "status": "draft",
  "validation_errors": [
    {"field": "make_key", "code": "MAKE_NOT_FOUND", "message": "make_key master data’da yok"}
  ],
  "next_actions": ["fix_form", "upload_media"]
}
```

## 4) Detail
### GET `/listings/vehicle/{id}`

Response 200:
```json
{
  "id": "<uuid>",
  "status": "published",
  "country": "DE",
  "category_key": "otomobil",
  "vehicle": {
    "make_key": "bmw",
    "model_key": "3-serie",
    "year": 2020
  },
  "attributes": {
    "mileage_km": 85000,
    "price_eur": 15000,
    "fuel_type": "electric",
    "transmission": "automatic",
    "condition": "used"
  },
  "media": [
    {
      "media_id": "<uuid>",
      "url": "/media/listings/<id>/<file>",
      "is_cover": true,
      "width": 1200,
      "height": 800
    }
  ]
}
```

## Hata kodları
- 401/403: auth
- 404: listing not found
- 422: publish guard fail
