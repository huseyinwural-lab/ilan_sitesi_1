# Structured Logging Implementation Plan

**Library:** `structlog`
**Target Format:** JSON (Single Line)

## 1. Schema Definition
Every log entry MUST contain:
```json
{
  "timestamp": "2026-02-12T17:05:00.123Z",
  "level": "INFO",
  "service": "backend-api",
  "request_id": "c6c607... (UUID)",
  "event": "listing_published",
  "user_id": "u-123", 
  "data": { ... }
}
```

## 2. Implementation Steps
1.  **Middleware:** Create `StructlogMiddleware`.
    -   Generate/Extract `X-Request-ID`.
    -   Bind `request_id` to context contextvar.
2.  **Configuration:**
    -   Dev Env: `ConsoleRenderer` (Pretty colors).
    -   Prod Env: `JSONRenderer`.
3.  **Refactoring:**
    -   Create `logger = structlog.get_logger()`.
    -   Replace `logger.info(f"User {u} logged in")` -> `logger.info("user_logged_in", user=u)`.

## 3. Backward Compatibility
-   Use `structlog`'s standard library bridge to capture logs from `uvicorn`, `sqlalchemy`, etc., and wrap them in the JSON format.
