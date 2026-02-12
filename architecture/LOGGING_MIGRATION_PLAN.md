# Logging Migration Plan v1 (Text -> Structured)

**Target:** P6 Sprint 1
**Library:** `structlog` (Python)

## Phase 1: Preparation
1.  **Install:** `pip install structlog python-json-logger`.
2.  **Config:** Configure `structlog` to output JSON.

## Phase 2: Middleware Implementation
Create `app/middleware/logging.py`:
-   **Request ID:** Extract `X-Request-ID` or generate uuid4. Set in `context`.
-   **Access Log:** Log every request start/finish with `method`, `path`, `status`, `latency`, `user_id`, `ip`.

## Phase 3: Replacement Strategy
-   **Global Logger:** Replace standard `logging.getLogger` with `structlog.get_logger`.
-   **Refactor:** Search/Replace `logger.info(f"Msg {var}")` -> `logger.info("Msg", var=var)`.
-   **Legacy Fallback:** Configure standard library bridge to catch libraries using standard `logging` and wrap them in JSON.

## Phase 4: Schema Documentation
**Standard Fields:**
```json
{
  "level": "info",
  "timestamp": "iso8601",
  "request_id": "uuid",
  "event": "event_name",
  "user_id": "optional",
  "data": {}
}
```
