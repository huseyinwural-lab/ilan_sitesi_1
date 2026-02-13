# Rate Limit Enforcement Report v1

**Target:** Public Search (`/api/v2/search`)

## 1. Policy
-   **Tier:** IP-Based (Anonymous)
-   **Limit:** 100 req/min.
-   **Burst:** 10 reqs (Token Bucket).

## 2. Guardrails
-   **Max Page Size:** 100 items.
-   **Max Filters:** 10 attributes.
-   **Max Range:** 5 range queries.

## 3. Verification
-   [ ] **Test:** Send 101 requests. Result: 101st is `429`.
-   [ ] **Test:** Send `page_size=500`. Result: `400 Bad Request` or Cap at 100.
