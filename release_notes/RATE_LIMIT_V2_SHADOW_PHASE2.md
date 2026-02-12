# Rate Limit v2: Shadow Mode Phase 2

**Status:** ACTIVE
**Date:** 2026-02-13

## 1. Configuration
-   `RATE_LIMIT_BACKEND`: `REDIS`
-   `RATE_LIMIT_ENFORCE`: `FALSE` (Shadow Mode)
-   `LOG_MISMATCH`: `TRUE`

## 2. Goal
Verify `RedisRateLimiter` accuracy against `MemoryRateLimiter` without blocking users.

## 3. Metrics to Watch (48h Window)
1.  **Hit Mismatch Rate:**
    -   formula: `abs(redis_count - memory_count) / redis_count`
    -   *Target:* < 5% (Variance due to cluster skew is expected).
2.  **Redis Latency:**
    -   *Target:* p99 < 10ms.
3.  **Error Rate:**
    -   *Target:* 0 connection errors.

## 4. Cutover Thresholds
If after 48h:
-   Redis p99 Latency < 20ms
-   No "Fail-Open" alerts triggered
-   User complaints = 0

**THEN:** Proceed to `RATE_LIMIT_ENFORCE = TRUE`.
