# P6 Monitoring Dashboard Spec

**Tool:** Grafana / Datadog

## Panel 1: Security & Abuse (Rate Limits)
-   **Type:** Time Series
-   **Metric:** `rate_limit_hits_total`
-   **Group By:** `status` (allowed/blocked), `tier` (ip/user).
-   **Alert:** Spike in `blocked` > 20% baseline.

## Panel 2: Revenue Health (Fail-Fast)
-   **Type:** Stat / Gauge
-   **Metric:** `pricing_error_total` (HTTP 409).
-   **Color:** Red if > 0.
-   **Drilldown:** Table showing `country` causing the error.

## Panel 3: Expiry Job Health
-   **Type:** Table
-   **Columns:** `Last Run Time`, `Duration`, `Items Processed`, `Status`.
-   **Alert:** If `Last Run Time` > 25 hours.

## Panel 4: System Vitals
-   **Type:** Time Series
-   **Metrics:** API Latency (p50, p95, p99), Error Rate (5xx).
