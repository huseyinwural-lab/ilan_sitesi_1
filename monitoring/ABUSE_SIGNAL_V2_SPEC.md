# Abuse Signal V2 Spec

**Goal:** Richer context in logs for security analysis.

## 1. Log Enrichment
When `429` occurs, log:
```json
{
  "event": "rate_limit_exceeded",
  "tier": "STANDARD",
  "limit_configured": 60,
  "burst_used": 5,
  "user_id": "u-123",
  "ip_risk_score": 0.0,
  "window_remaining": 45
}
```

## 2. New Metrics
-   `rate_limit_burst_utilization`: Histogram of how deep into the burst bucket users go.
-   `rate_limit_tier_distribution`: Counter of requests per tier.

## 3. Anomaly Detection
-   **Condition:** If `tier=STANDARD` and `429_count > 100/hour` -> Flag User ID for Review.
-   **Alert:** "Potential Account Compromise / Script Abuse".
