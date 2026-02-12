# Go-Live Approval Sheet (v1.5.0)

**Target Env:** Production
**Date:** 2026-02-12

## 1. System Checks
- [ ] **Timezone:** Container/Host time is UTC. `date` command verified.
- [ ] **Logging:** stdout/stderr capturing is active and shipped to centralized logging.
- [ ] **Database:** Migrations applied (`alembic upgrade head`). `alembic current` matches code.

## 2. Feature Verification
- [ ] **Pricing Gate:**
    - Test: Attempt publish without Price Config -> Verify `409 Conflict`.
    - Test: Attempt publish with Valid Config -> Verify `200 OK` & Invoice generated.
- [ ] **Rate Limiting:**
    - Test: Hit `/auth/login` 21 times -> Verify `429 Too Many Requests`.
    - Check headers: `Retry-After` is present.
- [ ] **Expiry Job:**
    - Test: Run `./start_cron.sh` manually. Verify exit code 0 and audit log entry.

## 3. Data Integrity
- [ ] **Seed Data:**
    - `VatRate` exists for all active countries (DE, FR, etc.).
    - `CountryCurrencyMap` populated.
    - `PriceConfig` exists for Dealers.
- [ ] **Indexes:** Verify `ix_dealer_subscriptions_status_end_at` exists in Prod DB.

## 4. Operational Readiness
- [ ] **Alerts:** 409 Rate > 0 triggers warning. 429 Rate > 1% triggers warning.
- [ ] **Runbook:** Support team has access to `/ops/RUNBOOK.md`.

**Approval Status:** ⬜ PENDING | ✅ APPROVED | ❌ REJECTED
**Signed Off By:** _________________________
