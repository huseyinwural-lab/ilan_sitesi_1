# AF Sprint 1 Tickets (Draft)

## AF2 — Risk/Ban
1. **AF2-1:** Add `users.risk_level` enum (low/medium/high)
   - AC: migration + model + API payload returned
   - Evidence: migration + curl get/update

2. **AF2-2:** Admin risk level update endpoint + audit
   - AC: `PATCH /admin/users/{id}/risk-level` + `RISK_LEVEL_UPDATED` audit
   - Evidence: audit log entry

3. **AF2-3:** Admin UI risk level control (Dealers/Admin Users)
   - AC: dropdown + save state + audit evidence

4. **AF2-4:** Ban/suspend guard + reason enforced (verify)
   - AC: suspend requires reason, login blocked for suspended user

## AF3 — Dealer Verification
5. **AF3-1:** Admin verification toggle endpoint + audit
   - AC: update `dealer_profiles.verification_status` with audit

6. **AF3-2:** Dealer panel badge
   - AC: verified badge visible when status=verified

## AF4 — Moderation Bulk + Filters
7. **AF4-1:** Bulk approve/reject UI polish + audit confirm
   - AC: multi-select + reason required

8. **AF4-2:** Moderation filters (status/category/date range)
   - AC: backend supports filters + UI fields

9. **AF4-3:** Large dataset test scenario
   - AC: pagination/filter performance check

## AF1 — Monetization
10. **AF1-1:** Plan validation guards (quota min/max, discount 0–100)
    - AC: server validation + UI parity

11. **AF1-2:** Dealer plan override audit parity
    - AC: audit log + UI confirmation

## AF5 — Finance Widgets
12. **AF5-1:** Admin dashboard widgets UI
    - AC: active subs, revenue MTD, active showcase count shown via API
