# Pricing Engine Contract V1 (Scaffold)

**Tarih:** 2026-02-25
**Not:** Parça 1 kapsamı sadece iskelet + kontrat freeze. Business logic Parça 2/3'te eklenecek.

## Admin Routes

### GET /api/admin/pricing/campaign
**Response (placeholder):**
```json
{
  "status": "not_implemented",
  "pricing_campaign_mode": {
    "is_active": false,
    "start_at": null,
    "end_at": null,
    "scope": "both"
  }
}
```

### PUT /api/admin/pricing/campaign
**Body:**
```json
{
  "is_active": true,
  "start_at": "2026-03-01T00:00:00Z",
  "end_at": "2026-03-31T00:00:00Z",
  "scope": "individual"
}
```
**Response (placeholder):**
```json
{
  "status": "not_implemented",
  "message": "Pricing campaign policy scaffold",
  "payload": { "...": "..." }
}
```

## Public Routes

### POST /api/pricing/quote
**Body:**
```json
{
  "user_type": "individual",
  "listing_count_year": 2,
  "listing_type": "listing"
}
```
**Response (placeholder):**
```json
{
  "status": "not_implemented",
  "message": "Pricing quote scaffold",
  "payload": { "...": "..." }
}
```

### GET /api/pricing/packages
**Response (placeholder):**
```json
{
  "status": "not_implemented",
  "packages": []
}
```

## Parametreler
- **scope:** `individual | corporate | both`
- **user_type:** `individual | corporate`

Contract freeze: Parça 2/3'te bu şema korunacaktır.
