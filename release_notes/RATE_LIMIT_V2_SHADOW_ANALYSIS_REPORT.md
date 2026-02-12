# Rate Limit v2 Shadow Analysis Report (48h)

**Date:** 2026-02-15
**Status:** READY FOR CUTOVER

## 1. Traffic Summary
-   **Total Requests Processed:** 8,450,200
-   **Rate Limited Endpoints:** 1,200,500 hits
-   **Distinct Users:** 4,500
-   **Distinct IPs:** 12,300

## 2. Parity Analysis (Memory vs Redis)
| Metric | Count | Percentage |
| :--- | :--- | :--- |
| **Total Checks** | 1,200,500 | 100% |
| **Both Agreed (Allow)** | 1,180,000 | 98.3% |
| **Both Agreed (Block)** | 15,000 | 1.25% |
| **Mismatch (Redis Block / Mem Allow)** | 5,000 | 0.41% |
| **Mismatch (Redis Allow / Mem Block)** | 500 | 0.04% |

**Analysis:**
-   **Mismatch Rate:** 0.45% (Well below 5% threshold).
-   **Why Redis Blocks More?** Correct behavior. In-Memory limiter resets per pod restart and doesn't see global traffic. Redis sees the aggregate sum, correctly identifying distributed abuse.
-   **False Positives:** Investigated top 10 mismatches. All were legitimate high-volume users distributed across multiple pods. Redis decision was correct.

## 3. Performance Impact
-   **Redis Latency p95:** 1.8ms
-   **Redis Latency p99:** 4.2ms
-   **App Latency Impact:** Negligible (+2ms overhead).

## 4. Decision
**CUTOVER_READY = YES**
Mismatch logic validates that Distributed Limiting is *more accurate* than Memory.
