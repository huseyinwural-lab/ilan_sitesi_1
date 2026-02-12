# Prod Monitoring Checklist

## 1. Metrics to Watch (Datadog/Prometheus)

### A. Critical (Wake up call)
-   **`pricing_fail_fast_count` (HTTP 409 on POST /listings):**
    -   **Threshold:** > 0
    -   **Meaning:** Revenue is blocked because Admin forgot Configs.
-   **`expiry_job_status`:**
    -   **Threshold:** != 0 (Exit Code)
    -   **Meaning:** Subscriptions are not expiring; free usage risk.

### B. Warning (Investigate)
-   **`rate_limit_block_count` (HTTP 429):**
    -   **Threshold:** > 1% of total traffic.
    -   **Meaning:** Potential attack OR Limits are too tight for legit users.
-   **`listing_publish_success_rate`:**
    -   **Threshold:** < 95%
    -   **Meaning:** General system instability.

## 2. Log Queries
-   `service:backend status:error "PricingConfigError"`
-   `service:backend "SYSTEM_EXPIRE"` (Confirm daily execution)
-   `service:backend status:warn "Rate Limit Exceeded"`

## 3. Dashboards
-   **Revenue Ops:** Valid Listings Created vs. Failed (409).
-   **Security:** Top blocked IPs (Rate Limit).
