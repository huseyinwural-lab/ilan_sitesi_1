# Rate Limit v2 Shadow Mode Report

**Goal:** Validate Redis-based Rate Limiter without affecting users.

## 1. Configuration
-   **Mode:** `SHADOW`
-   **Enforce:** `False` (Fail-Open)
-   **Backend:** Redis (Primary), Memory (Comparison)

## 2. Validation Steps
1.  **Feature Flag:** Enable `RL_SHADOW_MODE=True`.
2.  **Comparison Logic:**
    -   On Request: Increment Memory Counter & Redis Counter.
    -   Log `rate_limit_shadow_result`:
        ```json
        {
          "memory_blocked": false,
          "redis_blocked": false,
          "match": true,
          "redis_latency_ms": 2.4
        }
        ```
3.  **Data Collection:** Run for 48 Hours.

## 3. Analysis Plan
-   **Hit Mismatch:** Calculate % of requests where Memory and Redis disagreed.
    -   *Acceptable:* < 5% (Due to distributed nature vs local memory).
-   **Latency Histogram:** p95 and p99 of Redis operations.
-   **Error Rate:** Count of Redis Connection Errors.

## 4. Cutover Thresholds
-   Redis Error Rate < 0.01%
-   Redis p99 Latency < 20ms
-   Mismatch < 5%

*(Report to be filled after 48h execution)*
