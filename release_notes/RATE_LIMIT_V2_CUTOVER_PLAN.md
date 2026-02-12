# Rate Limit v2 Cutover Plan (Enforce Mode)

**Target Date:** 2026-02-15 10:00 UTC
**Owner:** DevOps / Backend

## 1. Canary Rollout (10%)
-   **Config:** Set `RATE_LIMIT_ENFORCE=True` on **1 Pod** (or Canary Deployment).
-   **Duration:** 2 Hours.
-   **Monitoring:**
    -   Watch `rate_limit_hits_total` on Canary pod.
    -   Watch User Support channel for "Unable to login/publish".
-   **Success Criteria:** No spike in 5xx errors.

## 2. Full Rollout (100%)
-   **Action:** Update ConfigMap / Env Var globally: `RATE_LIMIT_ENFORCE=True`.
-   **Verify:** Check logs for "Rate Limit Enforced (Redis)".

## 3. Legacy Removal Preparation
-   Wait 24h after Full Rollout.
-   If stable, merge PR #123 (Remove `MemoryRateLimiter` code).

## 4. Rollback Procedure
-   **Trigger:** Redis Latency > 50ms OR 5xx > 1%.
-   **Action:** Revert Env Var `RATE_LIMIT_ENFORCE=False` (Reverts to Fail-Open Shadow Mode).
-   **Emergency:** If Redis dead, `FAIL_OPEN` logic handles it automatically (Allow All).
