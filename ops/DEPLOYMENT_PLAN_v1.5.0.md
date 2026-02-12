# Production Deployment Plan (v1.5.0)

**Version:** v1.5.0-P5-HARDENING
**Target:** Production
**Date:** 2026-02-12

## 1. Pre-Deployment (T-minus 1 Hour)
- [ ] **Backup:** Take a full snapshot of the Production Database (`pg_dump`).
- [ ] **Notification:** Announce maintenance window (15 mins estimated).
- [ ] **Config Check:** Verify `RATE_LIMIT_ENABLED=True` and Stripe Keys in Prod Environment Variables.

## 2. Deployment Sequence
1.  **Stop Background Jobs:**
    -   Scale down `expiry-cron` deployment to 0.
2.  **Deploy Backend Code:**
    -   Push Docker Image `v1.5.0`.
    -   *Note: Application will restart.*
3.  **Database Migration:**
    -   Run `alembic upgrade head`.
    -   *Verify:* Index `ix_dealer_subscriptions_status_end_at` creation.
4.  **Health Check:**
    -   Hit `/api/health`. Expect `200 OK`.
5.  **Start Background Jobs:**
    -   Scale up `expiry-cron` to 1.

## 3. Post-Deployment Verification
- [ ] **Smoke Test:** Run the `PROD_SMOKE_TEST_REPORT` scenarios.
- [ ] **Logs:** Check for "PricingConfigError" or "RateLimitExceeded" spikes.

## 4. Rollback Plan (Emergency)
**Trigger:** High Error Rate (>5%) or Pricing Calculation Failures.

1.  **Revert Code:** Deploy previous image `v1.4.0`.
2.  **Revert Database (If schema broke):**
    -   `alembic downgrade -1` (Removes index/columns).
    -   *Worst Case:* Restore from Pre-Deploy Backup.
3.  **Disable Features (Partial Rollback):**
    -   If Rate Limit issues: Set `RATE_LIMIT_ENABLED=False`.
