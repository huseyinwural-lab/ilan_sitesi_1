## Admin Reports List API

### Endpoint
`GET /api/admin/reports`

### Query Params
- `status` (open | in_review | resolved | dismissed)
- `reason` (REPORT_REASON_ENUMS_V1)
- `listing_id`
- `skip`, `limit`
- `country` (country-scope)

### Response
```json
{
  "items": [
    {
      "id": "...",
      "listing_id": "...",
      "listing_title": "BMW 3-serie 2020",
      "reason": "spam",
      "reason_note": null,
      "status": "open",
      "country_code": "DE",
      "created_at": "...",
      "reporter_user_id": "...",
      "reporter_email": "...",
      "seller_email": "...",
      "seller_role": "dealer"
    }
  ],
  "pagination": {"total": 10, "skip": 0, "limit": 20}
}
```
