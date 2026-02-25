# Pricing Engine Contract V1 (Scaffold)

**Tarih:** 2026-02-25
**Not:** Parça 1 kapsamı sadece iskelet + kontrat freeze. Business logic Parça 2/3'te eklenecek.

## Admin Routes

### GET /api/admin/pricing/campaign
**Response:**
```json
{
  "policy": {
    "id": "...",
    "is_enabled": false,
    "start_at": null,
    "end_at": null,
    "scope": "all",
    "published_at": null,
    "version": 1
  },
  "active": false
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

### GET /api/admin/pricing/tiers
### PUT /api/admin/pricing/tiers
**Body:**
```json
{
  "rules": [
    { "tier_no": 1, "price_amount": 0, "currency": "EUR" },
    { "tier_no": 2, "price_amount": 100, "currency": "EUR" },
    { "tier_no": 3, "price_amount": 200, "currency": "EUR" }
  ]
}
```

### GET /api/admin/pricing/packages
### PUT /api/admin/pricing/packages
**Body:**
```json
{
  "packages": [
    {
      "name": "Vantage 20",
      "listing_quota": 20,
      "package_duration_days": 90,
      "package_price_amount": 500,
      "currency": "EUR",
      "is_active": true
    }
  ]
}
```

## Public Routes

### POST /api/pricing/quote
**Body:**
```json
{
  "user_type": "individual"
}
```
**Response (Part 3):**
```json
{
  "pricing_mode": "campaign",
  "override_active": true,
  "quote": {
    "type": "tier",
    "amount": 0,
    "currency": "EUR",
    "duration_days": 90,
    "requires_payment": false,
    "listing_no": 1
  }
}
```

### GET /api/pricing/packages
**Response:**
```json
{
  "packages": [
    { "id": "...", "name": "Vantage 20", "listing_quota": 20, "price_amount": 500 }
  ]
}
```

## Parametreler
- **scope:** `individual | corporate | all`
- **user_type:** `individual | corporate`

Contract freeze: Parça 2/3'te bu şema korunacaktır.
