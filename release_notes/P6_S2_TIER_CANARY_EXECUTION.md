
# P6 Sprint 2: Tier Canary Execution

**Date:** 2026-02-18
**Traffic:** 10%

## 1. Metrics
-   **429 Rate:** 0.5% (Stable).
-   **5xx Rate:** 0.02% (No regression).
-   **Redis Latency:** 1.9ms p95.

## 2. Findings
-   **Premium:** Verified VIP Dealer `d-999` publishing 150 listings/min without block.
-   **Standard:** Verified Spammer IP blocked at 60/min.

## 3. Rollback Test
-   Toggled `TIER_LIMIT_ENABLED=False`.
-   System reverted to `60/min` global.
-   Re-enabled successfully.

**Decision:** CANARY_PASS = YES
