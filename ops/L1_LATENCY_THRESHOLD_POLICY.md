# Latency Threshold Policy

## 1. Targets (P95)
*   **Search API**: 800ms.
*   **Detail API**: 600ms.
*   **Static Assets**: 100ms (CDN).

## 2. Monitoring
*   **Tool**: APM (Application Performance Monitoring) / Logs.
*   **Alert**: If P95 > 1500ms for 5 minutes -> Slack Alert to DevOps.

## 3. Mitigation (If Alert Triggered)
1.  **Check DB CPU**: If high -> Scale Read Replica.
2.  **Check Redis**: If full -> Flush non-critical keys.
3.  **Disable Heavy Features**: Turn off `ML Ranking` (fallback to SQL sort).
