# Search Filter API v2 Contract (Final)

**Status:** FROZEN
**Version:** v2.0.0
**Endpoint:** `GET /api/v2/search`

## 1. Request Parameters
| Name | Type | Description |
| :--- | :--- | :--- |
| `q` | string | Free-text search (Title, Description). Max 100 chars. |
| `category_slug` | string | Category Slug (e.g. `smartphones`). |
| `sort` | enum | `date_desc`, `price_asc`, `price_desc`. Default `date_desc`. |
| `page` | int | 1-based index. Default 1. |
| `limit` | int | Items per page. Default 20. Max 100. |
| `price_min` | int | Filter range. |
| `price_max` | int | Filter range. |
| `attrs` | json | Map of filters. `{"brand": ["apple"], "screen_size": {"min": 5}}`. |

## 2. Facet Response Schema
The `facets` object in response follows this structure:
```json
"facets": {
  "brand": [
    { 
      "value": "apple", 
      "label": "Apple", 
      "count": 42, 
      "selected": true 
    },
    { "value": "samsung", "label": "Samsung", "count": 15, "selected": false }
  ],
  "screen_size": { 
    "min": 4.5, 
    "max": 6.9,
    "unit": "inch" 
  }
}
```

## 3. Error Behavior
-   **Invalid JSON in `attrs`:** `400 Bad Request`.
-   **Unknown Attribute Key:** Ignored (Soft fail).
-   **Category Not Found:** Treated as Root search (or 404 if strict). *Decision: Treated as Global Search.*
