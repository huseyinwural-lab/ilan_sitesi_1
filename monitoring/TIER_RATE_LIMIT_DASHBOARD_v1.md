# Tier Rate Limit Dashboard v1

**Tool:** Grafana

## Panel 1: Tier Traffic
-   **Viz:** Stacked Area Chart.
-   **Query:** `sum(rate(rate_limit_hits_total{status="allowed"}[5m])) by (tier)`
-   **Goal:** Visualize business growth (Premium usage vs Standard).

## Panel 2: Block Rate by Tier
-   **Viz:** Multi-Line Chart.
-   **Query:** `sum(rate(rate_limit_hits_total{status="blocked"}[5m])) by (tier)`
-   **Alert:** If `tier=PREMIUM` block rate > 0 -> **CRITICAL**.

## Panel 3: Burst Usage
-   **Viz:** Heatmap.
-   **Metric:** `rate_limit_burst_utilization`.
-   **Goal:** Tune burst parameters.
