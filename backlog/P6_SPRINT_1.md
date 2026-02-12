# P6 Sprint 1 Backlog: Observability & Distributed Scale

**Goal:** Establish deep visibility and prepare for Horizontal Scaling.

## 1. High Priority (P0)
-   **Story: Distributed Rate Limiting (Redis)**
    -   **Task:** Replace in-memory `_rate_limit_store` with `redis-py`.
    -   **Task:** Implement Lua script for atomic sliding window.
    -   **Task:** Add `REDIS_URL` to config.
-   **Story: Structured Logging (JSON)**
    -   **Task:** Integrate `structlog` or `python-json-logger`.
    -   **Task:** Ensure `correlation_id` is propagated in all logs.
    -   **Task:** Log `pricing_context` (Input/Output) for every calculation.

## 2. Medium Priority (P1)
-   **Story: Expiry Job History**
    -   **Task:** Create `job_execution_history` table.
    -   **Task:** Update `expiry_worker` to write start/end times and summary to DB (Persistent record, not just AuditLog).
-   **Story: Admin Dashboard Widgets**
    -   **Task:** Backend API for `GET /api/admin/stats/rate-limits`.
    -   **Task:** Backend API for `GET /api/admin/stats/pricing-errors`.

## 3. Tech Debt (P2)
-   **Task:** Refactor `tests/test_p4_dealer.py` to remove hardcoded Stripe mocks and use the new Pricing fixtures.
