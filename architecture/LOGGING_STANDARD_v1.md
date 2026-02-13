# Logging Standard v1

**Library:** `structlog`
**Format:** JSON (Production), Console (Dev)

## 1. Schema
```json
{
  "timestamp": "ISO8601",
  "level": "INFO",
  "request_id": "uuid",
  "user_id": "uuid", // Optional
  "endpoint": "/api/v2/search",
  "method": "GET",
  "status_code": 200,
  "latency_ms": 45,
  "event": "http_request",
  "data": { ... }
}
```

## 2. Rules
-   **PII Redaction:** Emails, passwords, tokens MUST be masked `***`.
-   **Levels:**
    -   `INFO`: Business events (Listing created), Request logs.
    -   `WARN`: 4xx Errors, Business Rule Violations (Quota full).
    -   `ERROR`: 5xx Errors, DB Connection failures.
