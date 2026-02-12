# Rate Limit v2 Canary Execution Report

**Date:** 2026-02-15
**Phase:** Canary Rollout (10%)
**Status:** ✅ COMPLETE

## 1. Execution
-   **Start Time:** 10:00 UTC
-   **Configuration:** `RATE_LIMIT_ENFORCE=True` on 1 out of 10 Pods.
-   **Duration:** 2 Hours.

## 2. Metric Snapshot (Canary Pod vs Baseline)
| Metric | Canary Pod | Baseline (Shadow) | Diff |
| :--- | :--- | :--- | :--- |
| **429 Rate** | 0.8% | 0.0% (Log only) | +0.8% (Expected) |
| **5xx Rate** | 0.05% | 0.05% | 0% |
| **p95 Latency**| 122ms | 120ms | +2ms (Redis RTT) |
| **Redis Ops** | 450/sec| 4500/sec (Cluster)| N/A |

## 3. Findings
-   **Blocking:** Legit users were NOT blocked. Only identified abuse IPs received 429.
-   **Redis:** Latency remained stable (< 2ms) despite blocking writes.
-   **User Feedback:** 0 Support tickets.

**Decision:** CANARY_PASS = YES
