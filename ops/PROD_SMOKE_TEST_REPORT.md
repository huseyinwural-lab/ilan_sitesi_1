# Prod Smoke Test Report

**Target:** Production
**Time:** Post-Deploy

## 1. Admin Access
-   [ ] Login as `super_admin`.
-   [ ] Navigate to "Ticari Üyeler". Verify Table loads.

## 2. Critical Flow (DEF-001 Verification)
-   [ ] Pick Test Dealer `d-test`.
-   [ ] Check current limit (Standard).
-   [ ] Change Tier -> Premium.
-   [ ] **Action:** Send 70 requests/min via Postman.
-   [ ] **Expect:** 200 OK (Not Blocked).

## 3. Observability
-   [ ] Check Dashboard: "Total Users" > 0.
-   [ ] Check Logs: `ADMIN_CHANGE_TIER` appears in Kibana/Datadog.
