# P6 Observability Design (v1)

## 1. Structured Logging Standard
**Format:** JSON (New line delimited)
**Required Fields:**
- `timestamp`: ISO 8601 UTC
- `level`: INFO, WARN, ERROR
- `correlation_id`: Unique Request ID (propagated from LB or generated).
- `user_id`: (If auth)
- `event`: Machine-readable event name (e.g., `pricing_calculated`).

**Example:**
```json
{
  "timestamp": "2026-02-12T10:00:00Z",
  "level": "INFO",
  "correlation_id": "req-123",
  "user_id": "user-456",
  "event": "pricing_calculated",
  "data": {
    "source": "paid_extra",
    "amount": 5.00,
    "currency": "EUR"
  }
}
```

## 2. Key Traces & Events
- **Pricing:** `pricing_calculation_start`, `pricing_calculated`, `pricing_config_missing` (ERROR).
- **Rate Limit:** `rate_limit_exceeded` (WARN) - include IP and Endpoint.
- **Expiry Job:** `expiry_job_start`, `expiry_job_summary` (count), `expiry_job_error`.

## 3. Metrics (Prometheus Style)
- `http_requests_total{method, endpoint, status}`
- `rate_limit_hits_total{tier, endpoint}`
- `pricing_failures_total{reason="config_missing|concurrency"}`
- `job_execution_duration_seconds{job="expiry"}`

## 4. Alerting Thresholds
- **High Severity:**
    - `pricing_failures_total` > 0 (Immediate Config Check needed).
    - `job_execution_status` = FAILED.
- **Medium Severity:**
    - `rate_limit_hits_total` > 100/min (Potential Attack).
    - API Latency p95 > 500ms.
