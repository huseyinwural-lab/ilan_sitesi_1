# Listing Detail API Contract v1

## 1. Endpoint
`GET /api/v1/listings/{id}`

## 2. Response Structure
```json
{
  "id": "uuid",
  "title": "Luxury Apartment",
  "slug": "luxury-apartment-berlin",
  "price": 450000,
  "currency": "EUR",
  "description": "Full text description...",
  "status": "active",
  "published_at": "ISO-8601",
  "location": {
    "city": "Berlin",
    "district": "Mitte",
    "country": "DE",
    "accuracy": "approximate"
  },
  "media": [
    {"url": "/static/uploads/1.jpg", "type": "image"}
  ],
  "attributes": {
    "m2_gross": 85,
    "room_count": "2+1",
    "heating_type": "gas"
  },
  "seller": {
    "id": "uuid",
    "type": "commercial",
    "name": "Schmidt Immobilien",
    "rating": 4.8,
    "is_verified": true
  },
  "contact": {
    "phone_protected": true,
    "message_allowed": true
  },
  "seo": {
    "title": "Luxury Apartment in Berlin - Platform Name",
    "description": "85m2, 2+1 apartment for sale..."
  }
}
```

## 3. Error Codes
*   **404**: Not Found.
*   **410**: Gone (Deleted/Expired).
*   **301**: (Handled by Frontend via slug check)
