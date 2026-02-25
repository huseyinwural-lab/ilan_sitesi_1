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
    "is_enabled": false,
    "start_at": null,
    "end_at": null,
    "scope": "all"
  }
}
```

### PUT /api/admin/pricing/campaign
**Body:**
```json
{
  "is_enabled": true,
  "start_at": "2026-03-01T00:00:00Z",
  "end_at": "2026-03-31T00:00:00Z",
  "scope": "all"
}
```
**Response:**
```json
{
  "ok": true,
  "policy": {
    "id": "...",
    "is_enabled": true,
    "start_at": "...",
    "end_at": "...",
    "scope": "all",
    "published_at": "...",
    "version": 2
  },
  "active": true
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
**Response (Part 2):**
```json
{
  "pricing_mode": "campaign",
  "override_active": true,
  "warning": "override_active_no_rules",
  "fallback": "default_pricing",
  "quote": {
    "status": "not_implemented",
    "message": "Campaign override active; default pricing fallback"
  }
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
- **scope:** `individual | corporate | all`
- **user_type:** `individual | corporate`

Contract freeze: Parça 2/3'te bu şema korunacaktır.
