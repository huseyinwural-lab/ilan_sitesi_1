# Exception Handler Rollout Report

**Status:** PENDING IMPLEMENTATION

## 1. Handlers to Implement
-   `RequestValidationError` -> `422 validation_error`
-   `HTTPException` -> Maps status code to Taxonomy.
-   `StarletteHTTPException` -> Catch 404/405/etc.
-   `Exception` (Generic) -> `500 internal_server_error`.

## 2. Middleware Integration
-   Must inject `correlation_id` from Context.
-   Must log `500` errors with Traceback (but hide from response).
