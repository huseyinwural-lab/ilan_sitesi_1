# Production Runbook (v1.8.0)

**System:** Admin Panel & Pricing Engine
**Status:** LIVE
**On-Call:** DevOps / SRE Team

## 1. Incident Response Procedures

### A. Redis Failure (Rate Limiting Down)
-   **Trigger:** P1 Alert `Redis Connection Error > 1%` or `Fail-Open Event > 0`.
-   **Impact:** Rate limits are NOT enforced (Fail-Open). High abuse risk.
-   **Immediate Action:**
    1.  Check Cloud Provider Status (AWS ElastiCache / Render).
    2.  If Primary Down: Verify Failover to Replica.
    3.  If Cluster Down:
        -   **Action:** Enable WAF "Under Attack" mode at Cloudflare level (Layer 7 mitigation).
        -   **Action:** Monitor DB Load (Application is unprotected).
-   **Resolution:** Restore Redis snapshot or restart instance. App reconnects automatically.

### B. Pricing Config Missing (Revenue Blocked)
-   **Trigger:** P1 Alert `pricing_fail_fast_count > 0`.
-   **Impact:** Users cannot publish listings (409 Conflict).
-   **Immediate Action:**
    1.  Check Logs for `PricingConfigError` to identify Country/Segment.
    2.  Login to Admin Panel -> Pricing Configurations.
    3.  **Fix:** Insert missing Price or VAT rate immediately.
    4.  **Verify:** Ask user to retry (Idempotent).

### C. Rate Limit Misconfiguration (False Positives)
-   **Trigger:** P2 Alert `429 Rate > 5%`.
-   **Immediate Action:**
    1.  Identify if Issue is Global or User-Specific.
    2.  **User-Specific:** Use Admin Panel > Abuse Watch > **Override Limit** (e.g., Set to 5000 for 1h).
    3.  **Global:** Update `app/core/config.py` (requires deploy) OR hot-patch Env Var `RL_STANDARD=1000` and restart pods.

## 2. Escalation Chain
1.  **Level 1 (Ops On-Call):** Triage & basic restart/config fix.
2.  **Level 2 (Backend Lead):** Logic bugs, Pricing Engine errors.
3.  **Level 3 (CTO/Product):** Business decisions (e.g., "Disable blocking during huge marketing campaign").

## 3. Weekly Operations Checklist
- [ ] Review `429` Top Offenders report.
- [ ] Verify Expiry Job ran successfully 7/7 days.
- [ ] Check Redis Memory fragmentation.
- [ ] Review Audit Logs for suspicious Admin actions (Tier changes).
