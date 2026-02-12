# Production Hardening Checklist (v1)

**Target:** P5 Deployment
**Owner:** DevOps / SRE

## Critical Checks (Blocking)
- [ ] **Timezone:** Verify `date` on host/container returns UTC. Application logic relies on `datetime.now(timezone.utc)`.
- [ ] **Database Indexes:** Verify `ix_dealer_subscriptions_status_end_at` exists (Run `alembic current`).
- [ ] **Cron Job:** Ensure `start_cron.sh` is scheduled (Kubernetes CronJob or Render Cron).
- [ ] **Logging:** stdout/stderr must be captured. Verify `SYSTEM_EXPIRE` logs appear in dashboard.

## Monitoring & Observability
- [ ] **Rate Limiting:** Monitor HTTP 429 count.
    -   *Alert:* If 429s > 1% of total traffic -> Investigate Abuse or Config.
- [ ] **Pricing Failures:** Monitor HTTP 409 count on `POST /listings`.
    -   *Alert:* Any 409 indicates missing revenue configuration.
- [ ] **Expiry Job:** Monitor exit code of the daily job.

## Configuration
- [ ] **Keys:** `STRIPE_API_KEY` and `STRIPE_WEBHOOK_SECRET` set in Prod Environment.
- [ ] **Rate Limits:** Verify `RATE_LIMIT_ENABLED=True` env var.
