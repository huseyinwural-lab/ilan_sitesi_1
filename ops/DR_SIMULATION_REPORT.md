# Disaster Recovery (DR) Simulation Report

**Date:** 2026-02-12
**Scenario:** Post-Deployment Failures

## Simulation 1: Expiry Job Failure
-   **Condition:** Cron job container crashes or hangs.
-   **Impact:** Expired subscriptions remain "active".
-   **Recovery Action:**
    1.  SSH into Backend Container.
    2.  Run `/app/backend/start_cron.sh` manually.
    3.  Verify: `SELECT count(*) FROM audit_logs WHERE action='SYSTEM_EXPIRE'`.
-   **Result:** Success. Job is idempotent and catches up.

## Simulation 2: Rate Limiter Blocking Legit Users
-   **Condition:** IP Limit (20/min) is too low for a corporate office (NAT).
-   **Impact:** Multiple users blocked.
-   **Recovery Action:**
    1.  Edit Env Var: `RATE_LIMIT_ENABLED=False` (Immediate Relief).
    2.  Restart Container.
    3.  (Long term): Increase `RL_AUTH_LOGIN` or implement Whitelist.
-   **Result:** Success. Traffic flows immediately after restart.

## Simulation 3: Wrong Pricing Config
-   **Condition:** Admin entered 0.00 EUR for Pay-Per-Listing.
-   **Impact:** Free listings (Revenue Leak).
-   **Recovery Action:**
    1.  Update `PriceConfig` in DB (set `is_active=False`).
    2.  Insert correct `PriceConfig`.
    3.  (Note): Code hot-reload not needed; Logic queries DB per request.
-   **Result:** Immediate fix.
