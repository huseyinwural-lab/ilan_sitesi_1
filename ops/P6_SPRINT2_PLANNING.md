# P6 Sprint 2 Planning

**Theme:** Abuse Hardening & Operational Excellence
**Start:** 2026-02-17
**Duration:** 2 Weeks

## 1. Objectives
1.  **Advanced Rate Limiting:** Implement Tiered Limits (Premium vs Standard) to support business growth.
2.  **Chaos Engineering:** Execute the Redis Chaos Test Plan.
3.  **Log Optimization:** Implement Sampling to control costs.

## 2. Backlog (Prioritized)
1.  **[Feature] Tiered Rate Limits:** Update `RedisRateLimiter` to accept dynamic limits based on User Role/Package.
2.  **[Ops] Redis Chaos Test:** Execute `REDIS_CHAOS_TEST_PLAN.md` in Stage.
3.  **[Ops] Log Sampling:** Configure `structlog` to sample 10% of successful INFO logs.
4.  **[Monitor] Expiry Job Dashboard:** Complete the missing visualization for Cron jobs.

## 3. Capacity
-   **Dev:** 2 FTE
-   **Ops:** 1 FTE

## 4. Entry Criteria
-   Sprint 1 Closed (`v1.6.0` tagged).
-   Prod Baseline Established.

## 5. Exit Criteria
-   Tiered Limits active in Prod.
-   Chaos Test Report Signed off.
-   Log volume reduced by 40% (via sampling).
