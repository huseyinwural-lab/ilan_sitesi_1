# P5-005: Subscription Expiry Job Specification

## 1. Ticket Set (Implementation Plan)

### 🎫 Ticket 1: Database & State Machine Preparation
- **Task:** Verify and optimize DB schema for high-performance expiry queries.
- **Details:**
  - Ensure `dealer_subscriptions` has composite index on `(status, end_at)` for fast filtering.
  - Define state transitions: `active` -> `expired`.
  - Ensure `updated_at` is refreshed on expiry.
- **Acceptance:**
  - `EXPLAIN ANALYZE` shows index usage for the expiry query.

### 🎫 Ticket 2: Expiry Worker Implementation
- **Task:** Create the background job logic.
- **File:** `app/jobs/expiry_worker.py`
- **Logic:**
  1. Select all `active` subscriptions where `end_at < NOW() (UTC)`.
  2. Perform batch update to set `status = 'expired'`.
  3. Create `AuditLog` entries for system action.
  4. (Optional) Trigger email notification event (stub for now).
- **Constraints:**
  - Must use `AsyncSession`.
  - Must be idempotent (running twice on same day is safe).

### 🎫 Ticket 3: Scheduler & Testing
- **Task:** Configure the schedule and write regression tests.
- **Details:**
  - If using Kubernetes/Render: Create `start_cron.sh` entry point.
  - Tests: `tests/test_p5_expiry.py`.
    - Scenario: Active sub passes end date -> Job runs -> Status becomes expired.
    - Scenario: Quota check fails for expired sub.
- **Acceptance:**
  - Job runs successfully.
  - Test coverage > 90% for worker logic.

## 2. Acceptance Checklist (DoD)
- [ ] **Schedule:** Job configured to run daily (e.g., 00:00 UTC).
- [ ] **Timezone:** Strict UTC usage for all comparisons.
- [ ] **Idempotency:** Re-running the job on already expired subscriptions does not create duplicate logs or errors.
- [ ] **State Integrity:** Expired subscriptions **cannot** be used for listing creation (checked via Pricing Service).
- [ ] **Audit Trail:** Every expiration action is logged in `audit_logs` with `action='SYSTEM_EXPIRE'`.
