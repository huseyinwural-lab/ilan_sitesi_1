# P25: Search Performance Audit Spec

## 1. Metrics to Audit
*   **Latency (P50, P95, P99)**: Measured at API Gateway level.
*   **Throughput**: Requests per Second (RPS) capacity.
*   **Cache Efficiency**: Redis Hit/Miss ratio.
*   **DB Load**: Slow query count (> 200ms).

## 2. Audit Tool (`audit_performance.py`)
*   **Source**: Application Logs + Live Probe.
*   **Method**:
    1.  Parse `ml_prediction_logs` for ML overhead.
    2.  Hit `/api/v1/search` with 100 concurrent requests (Locust integration).
    3.  Report stats.

## 3. Targets
| Metric | Current (Est) | Target |
| :--- | :--- | :--- |
| Search P95 | 800ms | 500ms |
| Detail P95 | 600ms | 300ms |
| Cache Hit | 10% | 40% |
