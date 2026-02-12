# P7 System Health Dashboard

**Component:** Admin Panel > Dashboard (Sidebar Widget)

## 1. Metrics
-   **Redis:** 🟢 ONLINE (p95: 2ms).
-   **DB:** 🟢 ONLINE (Connections: 45/100).
-   **Pricing:** 🟢 HEALTHY (Fail-fast: 0).
-   **Jobs:** 🟢 EXPIRY RUNNING (Last: 00:00 UTC).

## 2. Alarm Status
-   **Indicator:** Traffic Light system.
-   **Logic:**
    -   Red: Active P0 Alert (Redis Down, high 5xx).
    -   Yellow: Warning (High Latency, 429 spike).
    -   Green: Nominal.

## 3. Key Cardinality
-   Display: "Active Rate Keys: 27,450".
-   Trend: Up/Down arrow vs yesterday.
