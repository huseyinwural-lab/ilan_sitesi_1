# P20: Mobile Response Contract

## 1. Overview
Mobile networks are unreliable and often metered. We must minimize payload size by excluding unused fields.

## 2. Global Rules
- **Nulls**: Avoid nulls where possible. Use empty strings `""` or `0` for numbers if semantically safe.
- **Dates**: `YYYY-MM-DD` for display dates, ISO 8601 for logic.
- **Money**: Formatted String (`50.000 €`) preferred over raw number for simple display, or send both.

## 3. DTO Definitions

### 3.1. Listing Card (Feed)
Used in Home, Search, Favorites.
```json
{
  "id": "uuid",
  "title": "BMW 320i",
  "price": 50000,
  "currency": "EUR",
  "image_url": "https://cdn.../thumb.jpg",
  "location": "Berlin, DE",
  "date": "2024-02-16",
  "is_premium": true
}
```
**Size Target**: < 500 bytes per item.

### 3.2. Listing Detail
Used in Item Detail screen.
```json
{
  "id": "uuid",
  "title": "BMW 320i Sport Line",
  "price": {
    "value": 50000,
    "currency": "EUR",
    "formatted": "50.000 €"
  },
  "images": [
    {"url": "...", "type": "original"},
    {"url": "...", "type": "thumb"}
  ],
  "attributes": [
    {"label": "Year", "value": "2022"},
    {"label": "Km", "value": "45.000"}
  ],
  "description": "Clean car...", // Plain text or simplified HTML
  "seller": {
    "id": "uuid",
    "name": "Auto Hans",
    "type": "dealer", // or "individual"
    "rating": 4.8
  },
  "is_favorite": false
}
```

## 4. Exclusion List
Fields present in Web API but **EXCLUDED** from Mobile:
- `meta_tags` (SEO)
- `internal_notes`
- `views_history` (Graph data)
- `similar_listings` (Fetched via separate lazy call)
