# Error Response Standard v1

**Goal:** Consistent JSON errors.

## 1. Schema
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "Listing not found or inactive.",
    "request_id": "123-abc...",
    "details": { "id": "..." } // Optional
  }
}
```

## 2. Codes
-   `400`: `validation_error`, `bad_request`
-   `401`: `unauthorized`
-   `403`: `forbidden`, `quota_exceeded`
-   `404`: `not_found`
-   `409`: `conflict` (Config missing)
-   `429`: `rate_limit_exceeded`
-   `500`: `internal_server_error`
