# AD_WIZARD_SQL_MAPPING_CHECKLIST

## Amaç
DB açıldığında sürpriz yaşamamak için **DTO → SQL Listing** mapping kontrol listesi.

## Kaynaklar
- `server.py`: `_apply_listing_payload_sql` + `/v1/listings/vehicle` endpoints
- `models/moderation.py`: `Listing` modeli

## Mapping Checklist (DTO → SQL)
| DTO Alanı | SQL Alanı | Kaynak/Not |
|---|---|---|
| `title` / `core_fields.title` | `listings.title` | `_apply_listing_payload_sql` (trim) |
| `description` / `core_fields.description` | `listings.description` | `_apply_listing_payload_sql` (trim) |
| `price.amount` | `listings.price` | `_apply_listing_payload_sql` |
| `price.currency_primary` | `listings.currency` | `_apply_listing_payload_sql` |
| `country` | `listings.country` | create draft (`/v1/listings/vehicle`) |
| `category_id` | `listings.category_id` | **GAP:** şu an sadece `attributes.category_id` olarak yazılıyor |
| `dynamic_fields` | `listings.attributes.attributes` | JSON merge |
| `attributes` | `listings.attributes.attributes` | JSON merge |
| `vehicle` | `listings.attributes.vehicle` | JSON merge |
| `detail_groups` | `listings.attributes.detail_groups` | JSON |
| `modules` | `listings.attributes.modules` | JSON |
| `payment_options` | `listings.attributes.payment_options` | JSON |
| `media` (upload) | `listings.attributes.media` + `listings.images` | media upload endpoint |
| `make_id` / `model_id` | `listings.make_id` / `listings.model_id` | **GAP:** DTO’da varsa mapping eklenmeli |

## Açıklar (DB gelince kapatılacak)
1. **category_id → listings.category_id** map edilmiyor.
2. **make_id / model_id** DTO’dan SQL kolonlarına map edilmiyor.

## Aksiyon (DB Unblock Sonrası)
- `_apply_listing_payload_sql` içinde category_id + make_id + model_id mapping ekle.
- E2E: create → submit → public search görünürlük kontrolü.
