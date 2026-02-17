# Emlak Search API Contract v1

## 1. Endpoint
`GET /api/v1/search/real-estate`

## 2. Request Parameters (Query String)

### 2.1. Taxonomy (Zorunluya Yakın)
*   `country`: ISO Code (DE, TR).
*   `segment`: (konut, ticari, gunluk, arsa).
*   `transaction`: (satilik, kiralik).
*   `type`: Sub-category slug (daire, ofis, vb.).

### 2.2. Core Filters
*   `price_min` / `price_max`: Integer.
*   `currency`: EUR/TRY (Varsayılan: Country default).
*   `m2_min` / `m2_max`: Integer.
*   `room_min` / `room_max`: String (1+1, 2+1...).

### 2.3. Location & Radius
*   `city`: String.
*   `zip_code`: String.
*   `lat` / `lon`: Float (Radius için merkez).
*   `radius_km`: Integer (Varsayılan 10, Max 100).

### 2.4. Dynamic Filters
*   `attr_{key}`: `?attr_heating=gas&attr_balcony=true`.

### 2.5. Sorting & Pagination
*   `sort`: `newest` (default), `price_asc`, `price_desc`.
*   `cursor`: Pagination token.
*   `limit`: Page size (Default 20).

## 3. Response Structure

```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Berlin Mitte 2+1 Daire",
      "price": 450000,
      "currency": "EUR",
      "location": {
        "city": "Berlin",
        "district": "Mitte",
        "zip": "10115"
      },
      "specs": {
        "m2": 85,
        "rooms": "2+1"
      },
      "image_url": "...",
      "badges": ["commercial", "verified"],
      "published_at": "ISO-8601"
    }
  ],
  "meta": {
    "cursor": "next_token",
    "total_count": 150
  },
  "facets": {
    "rooms": [{"label": "2+1", "count": 50}, ...],
    "heating": [...]
  }
}
```
