# Exception Taxonomy v1

**Goal:** Standardized Error Codes for Frontend/API Clients.

## 1. Core Structure
```json
{
  "error": {
    "code": "resource_not_found",
    "message": "User friendly message",
    "request_id": "uuid",
    "details": {} // Optional validation errors
  }
}
```

## 2. Taxonomy Matrix
| Code | HTTP | Description |
| :--- | :--- | :--- |
| `validation_error` | 422 | Input failed Pydantic rules. |
| `bad_request` | 400 | Generic client error. |
| `unauthorized` | 401 | Missing/Invalid Token. |
| `forbidden` | 403 | RBAC or Scope violation. |
| `not_found` | 404 | Resource ID invalid. |
| `conflict` | 409 | Duplicate Key or State Mismatch. |
| `rate_limit_exceeded` | 429 | Throttled. |
| `internal_server_error` | 500 | Uncaught Exception. |

## 3. Domain Specific
| Code | HTTP | Domain | Description |
| :--- | :--- | :--- | :--- |
| `pricing_config_missing` | 409 | Pricing | No active config for context. |
| `quota_exceeded` | 403 | Commercial | Listing limit reached. |
| `invalid_filter` | 400 | Search | Attribute key unknown or malformed. |
| `query_too_complex` | 422 | Search | Too many filters/facets requested. |
