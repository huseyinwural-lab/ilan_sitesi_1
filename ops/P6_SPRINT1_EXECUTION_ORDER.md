# P6 Sprint 1: Execution Order & Mandate

**Phase:** P6 - Optimization & Observability
**Sprint:** 1
**Goal:** Establish Distributed Infrastructure (Redis) and Structured Visibility (JSON Logs).

## 1. Sprint Scope
### Included (In-Scope)
-   **Infrastructure:** Provisioning Managed Redis (HA/Multi-AZ).
-   **Rate Limiting:** Implementing `RedisRateLimiter` class (Shadow Mode only).
-   **Logging:** Migrating `stdout` to JSON using `structlog`.
-   **Middleware:** Request ID / Correlation ID propagation.

### Excluded (Out-of-Scope)
-   **Pricing Logic Changes:** No changes to calculation logic.
-   **Frontend:** No UI changes.
-   **New Features:** No new business features.

## 2. Deployment Sequence
1.  **Step 1: Redis Provisioning (Ops)**
    -   Provision Cluster/Instance.
    -   Validate Connectivity from Backend Pods.
2.  **Step 2: Log Pipeline (Ops/Dev)**
    -   Update Ingestion Agent (Filebeat/Fluentd) to expect JSON.
    -   Deploy Backend with `structlog` (v1).
3.  **Step 3: Shadow Mode Release (Dev)**
    -   Deploy code with `RATE_LIMIT_BACKEND="redis"` but `RATE_LIMIT_ENFORCE=False`.
    -   Verify Redis connectivity logs without blocking traffic.

## 3. Success Criteria (Definition of Done)
-   [ ] **Redis Latency:** p95 < 5ms (Internal network).
-   [ ] **Shadow Parity:** Rate Limit Mismatch < 1% (In-memory vs Redis counters).
-   [ ] **Log Format:** 100% of stdout logs are valid JSON.
-   [ ] **Correlation:** 100% of logs contain `request_id`.

**Authorization:** Sprint 1 is officially initiated.
