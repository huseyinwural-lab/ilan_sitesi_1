# Search Filter API v2 Contract Final

**Endpoint:** `GET /api/v2/search`

## 1. Request Parameters
| Param | Type | Description |
| :--- | :--- | :--- |
| `q` | string | Full-text search (Title, Desc). |
| `category_slug` | string | Filter by Category (and children). |
| `sort` | enum | `price_asc`, `price_desc`, `date_desc` (default). |
| `page` | int | Default 1. |
| `limit` | int | Default 20. Max 100. |
| `price_min` | int | |
| `price_max` | int | |
| `attrs` | dict | JSON-encoded string for attributes. |

**`attrs` Format:**
```json
{
  "brand_electronics": ["apple", "samsung"],  // Multi-Select
  "screen_size": {"min": 5, "max": 7},       // Range
  "shipping_available": true                 // Boolean
}
```

## 2. Response Structure
```json
{
  "items": [
    { "id": "...", "title": "iPhone 13", "price": 900, "currency": "EUR", "image": "..." }
  ],
  "facets": {
    "brand_electronics": [
      { "value": "apple", "label": "Apple", "count": 12, "selected": true },
      { "value": "samsung", "label": "Samsung", "count": 5, "selected": false }
    ],
    "screen_size": { "min": 4.0, "max": 13.0 } // Global bounds for range slider
  },
  "pagination": { "total": 17, "page": 1, "pages": 1 }
}
```
