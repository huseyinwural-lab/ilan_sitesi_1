# P6 Alarm Final Calibration

**Target:** Production Alerts
**Source:** Post-Cutover Data

## 1. Revised Thresholds
| Metric | Old | New | Rationale |
| :--- | :--- | :--- | :--- |
| **429 Rate** | > 1% | > 2% | 1% was too noisy during minor bot scans. |
| **Redis Latency** | > 20ms | > 10ms | p99 is consistent at 4ms. 10ms warns early. |
| **Fail-Open** | > 0 | > 0 | Keep Critical. |

## 2. False Alarm Tuning
-   **Suppress:** "High Connection" alert during deployment rolling update window (15m).
-   **Suppress:** 429 alerts from known Security Scanner IPs.

**Status:** ALARMS LIVE.
