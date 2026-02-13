# P7.0 Stabilization Backlog v1

**Phase:** System Hardening & Observability
**Status:** OPEN

## Epic 1: Observability Foundation
-   **Task:** Define JSON Logging Schema (`timestamp`, `request_id`, `user_id`, `data`).
-   **Task:** Implement `CorrelationIdMiddleware`.
-   **Criteria:** 100% of logs have `request_id`.

## Epic 2: API Contract Hardening
-   **Task:** Implement Global Exception Handler (`4xx`/`5xx` JSON Standard).
-   **Task:** Enforce `PaginationDeterminism` (Tie-breaker sorting).
-   **Criteria:** No unhandled 500s (HTML leaks). All lists stable.

## Epic 3: Security Guardrails
-   **Task:** Enforce `RateLimit` on `/api/v2/search`.
-   **Task:** Enforce Query Complexity Limits (Max 10 filters).
-   **Criteria:** Abuse simulation returns `429`.

## Epic 4: Performance Validation
-   **Task:** Create 10k Synthetic Listings.
-   **Task:** Run Load Test (Search + Filter).
-   **Task:** Audit Query Plans (`EXPLAIN ANALYZE`).
-   **Criteria:** p95 Search Latency < 150ms.
