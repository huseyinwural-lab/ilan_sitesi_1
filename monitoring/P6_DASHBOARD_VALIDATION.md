# P6 Monitoring Dashboard Validation

**Platform:** Grafana / Datadog
**Status:** VALIDATED

## 1. Panel Verification
-   [x] **Redis Latency:** Shows real-time `cmd_latency` from Redis Metrics.
-   [x] **Rate Limit Hits:** Shows `rate_limit_hits_total` grouped by `tier`.
    -   *Observation:* IP Tier (Login) shows regular background noise. User Tier shows peaks during business hours.
-   [x] **Pricing Fail-Fast:** Shows count of `409 Conflict`. Currently Flat 0 (Good).
-   [x] **Error Rate:** 5xx rate tracking correctly.
-   [x] **Expiry Job:** Shows "Last Execution" timestamp.

## 2. Alarm Tests
-   **Scenario:** Manually lowered threshold for "High 429 Rate" to 1 req/min.
-   **Result:** Slack Alert triggered within 1 minute.
-   **Action:** Reverted threshold to production value (>5%).

## 3. Sign-off
Dashboard is trusted for P6 operations.
