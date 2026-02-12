# P6 Sprint 2 Observability Extensions

## 1. New Dashboards
### A. Tier Performance
-   **Graph:** "Requests per Tier" (Stacked Bar).
    -   Series: `tier=basic`, `tier=premium`, `tier=admin`, `tier=ip`.
-   **Metric:** `rate_limit_hits_total`.

### B. Blocked by Segment
-   **Graph:** "429s by Customer Type".
-   **Goal:** Visualize if we are blocking paying customers (Premium) vs anonymous IPs.

## 2. Adaptive Thresholds
-   **Concept:** Instead of static `1%` error rate:
    -   IF `tier=premium` AND `429_count > 0` -> **Critical Alert**.
    -   IF `tier=ip` AND `429_count > 100` -> **Warning** (Likely bot).

## 3. Logs
-   Add `tier` field to structured logs.
-   Add `limit_allocated` field to logs (e.g., "User allowed 300").
