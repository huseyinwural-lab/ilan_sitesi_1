# P7 Admin Rate Monitoring Spec

**Component:** Admin Panel > Monitoring > Traffic

## 1. Visualizations
-   **Global 429 Rate:** Line chart showing % of requests blocked over last 24h.
    -   *Source:* Prometheus/CloudWatch API or Redis aggregate keys.
-   **Top Blocked Dealers:** Table listing Dealers with highest 429 counts.
-   **Burst Heatmap:** Visualization of token bucket consumption (Green=Empty, Red=Full).

## 2. Health Widgets
-   **Redis Latency:** "1.8ms" (Green if < 5ms).
-   **Fail-Open Events:** Count of Redis connection failures (Should be 0).

## 3. Implementation
-   **Backend:** `GET /api/admin/stats/rate-limits`
    -   Aggregates data from Redis keys `rl:stats:*`.
    -   Cached for 60s to prevent overloading Redis during monitoring.
