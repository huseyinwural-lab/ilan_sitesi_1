# Production Baseline Snapshot (v1.7.0)

**Date:** 2026-02-27
**Status:** REFERENCE

## 1. API Performance
| Metric | Value | Change vs v1.6.0 |
| :--- | :--- | :--- |
| **p50 Latency** | 46ms | +1ms (Lua overhead) |
| **p95 Latency** | 128ms | +3ms |
| **5xx Rate** | 0.02% | Stable |

## 2. Rate Limiting Efficiency
| Tier | Block Rate | Burst Usage (Avg) |
| :--- | :--- | :--- |
| **Standard** | 0.85% | 80% |
| **Premium** | 0.00% | 45% |
| **IP (Auth)** | 2.10% | N/A |

## 3. Infrastructure
-   **Redis Memory:** 1.4GB (Stable).
-   **Key Cardinality:** ~27,000 keys.
-   **Log Volume:** ~5.2 GB/day (Enriched Logs).

## 4. Alarm Baseline
-   **False Alarms:** 0 in last 7 days.
-   **Abuse Alerts:** ~2 valid alerts/day.
