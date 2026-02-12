# Post-Deployment Validation Report

**Environment:** Production
**Executor:** DevOps Team

## 1. Data Integrity Checks
- [ ] **Pricing Snapshot:** Create a test listing (Internal Admin). Verify `invoice_items` table has `price_config_version` populated.
- [ ] **Subscription State:** Manually check a subscription expected to expire today. Verify `status='expired'` after 00:00 UTC.

## 2. Functional Checks
- [ ] **Rate Limit:** Perform 5 rapid refresh requests. Verify headers `X-RateLimit-Remaining` decrement.
- [ ] **Fail-Fast:** Attempt to publish in a disabled country (if any). Verify `409 Conflict`.

## 3. Operational Checks
- [ ] **Cron:** Verify `expiry-cron` container is running and healthy.
- [ ] **Logs:** Verify logs are flowing to Central Logging (Splunk/Datadog) and are readable.
- [ ] **Timezone:** Verify application logs show UTC timestamps.

**Validation Status:** ⬜ PASS | ⬜ FAIL
