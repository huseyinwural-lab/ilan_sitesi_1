# Structured Logging v1 Activation

**Target:** Production
**Version:** v1.0 (JSON Standard)

## 1. Activation Steps
1.  **Deploy:** Update Backend image with `structlog` enabled.
2.  **Config:** Set `LOG_FORMAT=json` in Environment Variables.
3.  **Verification:** Check stdout for JSON formatted lines.

## 2. Validation Checklist
- [ ] **Correlation ID:** verify `X-Request-ID` from Load Balancer is propagated to `request_id` in logs.
- [ ] **Consistency:** Ensure `uvicorn` access logs and Application logs share the same format.
- [ ] **Schema:** Version `v1` is locked. No breaking schema changes allowed without RFC.

## 3. Sampling Policy
-   **ERROR/WARN:** 100% Retention.
-   **INFO (Business Events):** 100% Retention (e.g., `listing_published`).
-   **INFO (High Volume):** 10% Sampling (e.g., `health_check`, `metric_export`).
-   **DEBUG:** Disabled in Prod (0%).

## 4. Fallback
-   **Dev Environment:** `LOG_FORMAT=console` (Human readable colors) remains active for local development.
