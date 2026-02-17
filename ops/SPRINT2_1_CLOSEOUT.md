#+#+#+#+ SPRINT 2.1 Closeout — Admin Global Listing Yönetimi

## Kapsam
- Admin Global Listing Yönetimi (filtreler + aksiyonlar)
- Audit-first soft-delete ve force-unpublish

## API Contract
### GET /api/admin/listings
- Filters: `status`, `q`, `dealer_only`, `category_id`, `skip`, `limit`, `country` (country-scope)

### POST /api/admin/listings/{listing_id}/soft-delete
- Audit: `LISTING_SOFT_DELETE`

### POST /api/admin/listings/{listing_id}/force-unpublish
- Audit: `LISTING_FORCE_UNPUBLISH`

## Audit Events
- `LISTING_SOFT_DELETE`
- `LISTING_FORCE_UNPUBLISH`

## UI Kanıtı
- Screenshot: `/app/test_reports/admin_listings_updated.png`

## Test Komutları (örnek)
```bash
curl -X POST $REACT_APP_BACKEND_URL/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@platform.com","password":"Admin123!"}'

curl -X GET "$REACT_APP_BACKEND_URL/api/admin/listings?limit=5" \
  -H "Authorization: Bearer <TOKEN>"

curl -X POST $REACT_APP_BACKEND_URL/api/admin/listings/<LISTING_ID>/force-unpublish \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reason":"policy_violation"}'

curl -X POST $REACT_APP_BACKEND_URL/api/admin/listings/<LISTING_ID>/soft-delete \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"reason":"cleanup"}'
```
