# Search v2 Guardrails Enforced Report

**Endpoint:** `/api/v2/search`

## 1. Limits
-   `limit` (Page Size): Max 100.
-   `attrs` (Filter Count): Max 10 keys.
-   `category_slug` (Length): Max 50 chars.

## 2. Validation
-   If `limit > 100`: Return `422 validation_error`.
-   If `len(attrs) > 10`: Return `422 query_too_complex`.
