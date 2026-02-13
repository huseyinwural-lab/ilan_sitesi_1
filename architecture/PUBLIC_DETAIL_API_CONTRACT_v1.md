# Public Detail API Contract

**Document ID:** PUBLIC_DETAIL_API_CONTRACT_v1  
**Date:** 2026-02-13  
**Status:** 📝 DRAFT  

---

## 1. Endpoint
`GET /api/v2/listings/{id}`

**Parameters:**
- `id`: UUID (Required)
- `increment_view`: boolean (Optional, default=false)

---

## 2. Response Structure

```json
{
  "listing": {
    "id": "uuid",
    "title": "Clean BMW 320i",
    "slug": "clean-bmw-320i",
    "price": 1250000,
    "currency": "TRY",
    "description": "...",
    "status": "active", // active, sold, expired
    "created_at": "ISO8601",
    "updated_at": "ISO8601",
    
    "location": {
      "country": "TR",
      "city": "Istanbul",
      "district": "Kadikoy"
    },

    "media": [
      { "url": "...", "type": "image", "order": 0 }
    ],

    "attributes": [
      { 
        "group": "Specs", 
        "items": [
          { "key": "km", "label": "Kilometre", "value": "50.000", "unit": "km" },
          { "key": "fuel", "label": "Yakıt", "value": "Benzin" }
        ]
      }
    ],

    "seller": {
      "id": "uuid",
      "name": "Ahmet Y.", // Masked if private
      "type": "individual", // or dealer
      "dealer_name": "Auto Gallery" // null if individual
    },
    
    "breadcrumbs": [
      { "label": "Vasıta", "slug": "vehicle" },
      { "label": "Otomobil", "slug": "cars" }
    ]
  },
  
  "seo": {
    "title": "Clean BMW 320i - 1.250.000 TL",
    "description": "Istanbul Kadikoy satılık..."
  },

  "related": [
    // Simplified listing objects (limit 4)
  ]
}
```

---

## 3. Business Logic
- **View Count:** Increment async via Redis if `increment_view=true`.
- **Attribute Formatting:** Backend resolves Option IDs to Labels (localized).
- **Related Listings:** Query by `category_id` + `city` + `price_range` (+/- 20%).

---

## 4. Error Codes
- `404`: Listing not found.
- `410`: Listing inactive (and user is not owner/admin).
- `403`: Banned listing.
