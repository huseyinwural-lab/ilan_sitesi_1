# API Contract: Vehicle Master Data v1 (Final)

**Status:** FROZEN

## 1. Listing Create/Update
**Endpoint:** `POST /api/commercial/dealers/{id}/listings`
**Payload:**
```json
{
  "make_id": "uuid",
  "model_id": "uuid",
  "attributes": {
     // NO "brand" string
     // NO "model" string
     "year": 2020,
     "fuel_type": "diesel"
  }
}
```
**Validation:**
-   Backend MUST verify `make_id` exists.
-   Backend MUST verify `model_id` belongs to `make_id`.

## 2. Listing Read
**Endpoint:** `GET /api/listings/{id}`
**Response:**
```json
{
  "id": "...",
  "make": { "id": "...", "name": "BMW", "slug": "bmw" },
  "model": { "id": "...", "name": "3 Series", "slug": "3-series" },
  "attributes": { "year": 2020 ... } // Clean
}
```

## 3. Admin Management
-   **Create Make:** `POST /api/admin/vehicles/makes` (Super Admin).
-   **Delete:** `DELETE` is blocked. Use `PATCH {is_active: false}`.
