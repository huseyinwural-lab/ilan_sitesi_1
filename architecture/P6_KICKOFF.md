# P6 Sprint 1 Kickoff: Observability & Distributed Scale

**Start Date:** Immediately after Hypercare
**Focus:** Infrastructure Hardening & Visibility

## 1. Goals
1.  **Global Rate Limiting:** Eliminate the "Per-Pod Limit" risk by moving state to Redis.
2.  **Structured Logging:** Convert all logs to JSON for machine parsing and queryability.
3.  **Traceability:** End-to-End tracing (Correlation ID) from Nginx -> Backend -> DB.

## 2. Sprint Backlog
### High Priority (Must Have)
-   **Infra:** Provision Redis (Cluster/Failover).
-   **Dev:** Implement `RedisRateLimiter` class (replacing memory dict).
-   **Dev:** Integrate `structlog` library.
-   **Dev:** Add Middleware for `X-Request-ID` extraction/generation.

### Medium Priority
-   **Ops:** Dashboard for "Top 429 Clients".
-   **Dev:** Expiry Job Execution History table.

## 3. Definition of Done (Sprint 1)
-   Rate limits enforced globally across at least 2 replica pods.
-   Logs are JSON formatted in stdout.
-   Every log entry contains `request_id`.
