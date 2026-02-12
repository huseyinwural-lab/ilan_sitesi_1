# Backlog: Observability V2

**Priority:** P6
**Goal:** Deep visibility into Pricing and Scaling logic.

## 1. Pricing Decision Traces
- **Requirement:** Assign a unique `trace_id` to every `calculate_listing_fee` call.
- **Log:**
    - Input: `dealer_id`, `country`
    - Logic: `Free(Available) -> Sub(Exhausted) -> Overage(Applied)`
    - Output: `Price`, `VAT`, `Currency`
- **Use Case:** Debugging "Why was I charged?" support tickets.

## 2. Rate Limit Metrics
- **Requirement:** Expose Prometheus/OpenTelemetry metrics.
- **Metric:** `rate_limit_hits_total{endpoint="/login", status="allowed|blocked", tier="ip|user"}`
- **Metric:** `rate_limit_current_usage` (Histogram).

## 3. Expiry Job History
- **Requirement:** New DB Table `job_execution_history`.
- **Fields:** `job_name`, `started_at`, `finished_at`, `status`, `items_processed`, `log_summary`.
- **UI:** Admin Panel page to view job status history.

## 4. Payment Reconciliation
- **Requirement:** Dashboard showing `PaymentAttempt` vs `Invoice` vs `StripeEvent` mismatches.
