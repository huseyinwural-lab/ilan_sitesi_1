## Admin Reports Detail API

### Endpoint
`GET /api/admin/reports/{id}`

### Response (özet)
```json
{
  "id": "...",
  "listing_id": "...",
  "reason": "spam",
  "reason_note": null,
  "status": "open",
  "country_code": "DE",
  "listing_snapshot": {
    "id": "...",
    "title": "BMW 3-serie 2020",
    "status": "published",
    "price": 20000,
    "currency": "EUR"
  },
  "seller_summary": {
    "id": "...",
    "email": "seller@platform.com",
    "role": "dealer",
    "dealer_status": "active"
  },
  "reporter_summary": {
    "id": "...",
    "email": "user@platform.com",
    "role": "individual"
  }
}
```
