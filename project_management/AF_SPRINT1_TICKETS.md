# AF Sprint 1 Tickets (Final)

## AF2 — Risk/Ban

### AF2-1: Add `users.risk_level` enum (low/medium/high)
- **Acceptance Criteria:** migration adds enum + column (default `low`), API payload includes `risk_level`
- **API Example:** `PATCH /api/admin/users/{id}/risk-level` → `{ ok: true, risk_level: "high" }`
- **RBAC:** `super_admin`, `moderator`
- **Audit:** `RISK_LEVEL_UPDATED`
- **Test Evidence:** curl response + audit log row + migration dry-run PASS log

### AF2-2: Admin risk level update endpoint + audit
- **Acceptance Criteria:** invalid risk_level rejected, audit event written with before/after
- **API Example:** `PATCH /api/admin/users/{id}/risk-level` payload `{ risk_level, reason }`
- **RBAC:** `super_admin`, `moderator`
- **Audit:** `RISK_LEVEL_UPDATED`
- **Test Evidence:** curl (400 + 200) + audit log + dry-run PASS

### AF2-3: Admin UI risk level control (Dealers/Admin Users)
- **Acceptance Criteria:** dropdown shows low/medium/high, save persists, success message
- **API Example:** UI uses `PATCH /api/admin/users/{id}/risk-level`
- **RBAC:** same as endpoint
- **Audit:** `RISK_LEVEL_UPDATED`
- **Test Evidence:** Playwright screenshot + audit log

### AF2-4: Ban/suspend guard + reason enforced
- **Acceptance Criteria:** suspend requires reason, suspension_until future-only, login blocked
- **API Example:** `POST /api/admin/users/{id}/suspend` payload `{ reason_code, reason_detail, suspension_until }`
- **RBAC:** `super_admin`, `moderator`
- **Audit:** existing `user_suspended` / `dealer_suspended`
- **Test Evidence:** curl (400 without reason) + 200 with reason + dry-run PASS

## AF3 — Dealer Verification

### AF3-1: Admin verification toggle endpoint + audit
- **Acceptance Criteria:** verified/unverified toggle persisted
- **API Example:** `PATCH /api/admin/dealers/{id}/verification` (TBD)
- **RBAC:** `super_admin`, `country_admin`
- **Audit:** `DEALER_VERIFIED` / `DEALER_UNVERIFIED`
- **Test Evidence:** curl + audit log

### AF3-2: Dealer panel badge
- **Acceptance Criteria:** verified badge visible when status=verified
- **API Example:** dealer profile payload includes `verification_status`
- **RBAC:** N/A (read)
- **Audit:** N/A
- **Test Evidence:** Playwright screenshot

## AF4 — Moderation Bulk + Filters

### AF4-1: Bulk approve/reject UI + audit confirm
- **Acceptance Criteria:** multi-select + reject reason required
- **API Example:** `POST /api/admin/moderation/bulk-reject` payload `{ listing_ids, reason }`
- **RBAC:** `super_admin`, `country_admin`, `moderator`
- **Audit:** item-level moderation audit
- **Test Evidence:** curl 400 without reason + 200 with reason + dry-run PASS

### AF4-2: Moderation filters (status/category/date range)
- **Acceptance Criteria:** backend supports new filters + UI fields
- **API Example:** `GET /api/admin/moderation/queue?status=...&category=...&date_from=...&date_to=...`
- **RBAC:** `super_admin`, `country_admin`, `moderator`
- **Audit:** N/A
- **Test Evidence:** filter results + pagination

### AF4-3: Large dataset test scenario
- **Acceptance Criteria:** pagination and filter performance validated
- **API Example:** same as AF4-2
- **RBAC:** same as AF4-2
- **Audit:** N/A
- **Test Evidence:** test report

## AF1 — Monetization

### AF1-1: Plan validation guards (quota min/max, discount 0–100)
- **Acceptance Criteria:** listing/showcase quota enforced; discount range enforced in DB
- **API Example:** `PUT /api/admin/plans/{id}` invalid quota → 400
- **RBAC:** `super_admin`, `finance`
- **Audit:** plan create/update (TBD)
- **Test Evidence:** curl 400 + dry-run PASS log

### AF1-2: Dealer plan override audit parity
- **Acceptance Criteria:** override writes `DEALER_PLAN_OVERRIDE`
- **API Example:** `POST /api/admin/dealers/{id}/plan`
- **RBAC:** `super_admin`, `country_admin`, `moderator`
- **Audit:** `DEALER_PLAN_OVERRIDE`
- **Test Evidence:** audit log row + dry-run PASS

## AF5 — Finance Widgets

### AF5-1: Admin dashboard widgets UI
- **Acceptance Criteria:** active subs, revenue MTD, active showcase count visible
- **API Example:** `GET /api/admin/dashboard/summary`
- **RBAC:** `super_admin`, `finance`, `country_admin`, `support`
- **Audit:** N/A
- **Test Evidence:** Playwright screenshot
