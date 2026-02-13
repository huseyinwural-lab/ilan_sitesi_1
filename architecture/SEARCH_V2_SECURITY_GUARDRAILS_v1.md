# Search v2 Security Guardrails v1

**Policy:** Abuse Prevention for Public Endpoint.

## 1. Rate Limiting
-   **Anonymous:** 100 req/min (IP Based).
-   **Authenticated:** 300 req/min (User Based).

## 2. Input Validation
-   `q`: Strip special chars, max 100 len.
-   `limit`: Hard cap at 100.
-   `page`: Hard cap at 1000 (Deep paging prevention).

## 3. Query complexity
-   Max 10 active attribute filters per request.
-   Reason: Prevents DB join explosion.
