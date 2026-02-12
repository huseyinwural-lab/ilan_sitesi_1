# P5-005: Expiry Job - Acceptance & Closure Report

**Status:** ✅ ACCEPTED / CLOSED
**Date:** 2026-02-12

## 1. Deliverables Verified
- [x] **Database Index:** `ix_dealer_subscriptions_status_end_at` created.
- [x] **Worker Logic:** `app/jobs/expiry_worker.py` correctly implements state transition (`active` -> `expired`).
- [x] **Idempotency:** Logic is safe to re-run (checks `status='active'` before update).
- [x] **Audit:** `SYSTEM_EXPIRE` logs generated.
- [x] **Tests:** `tests/test_p5_expiry.py` passed regression and logic checks.

## 2. Production Readiness Checklist (To be verified in Prod)
- [ ] **Timezone:** Ensure Host/Container timezone is UTC or DB connection forces UTC.
- [ ] **Logging:** Job stdout/stderr must be shipped to centralized logging (e.g., Datadog/CloudWatch).
- [ ] **Alerting:** If the job exits with non-zero code, an alert must trigger (Backlog Item created).
- [ ] **Data Integrity:** `end_at` field is populated for all subscriptions (checked via schema/migration).

## 3. Known Limitations
- The job currently processes all records in one batch. For >100k subscriptions, pagination (batch processing) will be needed.
