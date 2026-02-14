# Production Daily Healthcheck

**Document ID:** PRODUCTION_DAILY_HEALTHCHECK_v1  
**Date:** 2026-02-13  
**Status:** 📋 TEMPLATE  

---

## 1. Morning Routine (09:00 UTC)

### 1.1. Revenue Integrity
- [ ] **Stripe Dashboard:** Check for "Failed Payments" or "Disputes".
- [ ] **DB Reconciliation:** `SELECT count(*) FROM user_subscriptions WHERE status='active'` vs Stripe Active Subs.

### 1.2. System Health
- [ ] **Search P95:** Is it under 200ms? (Check CloudWatch/Grafana).
- [ ] **Error Rate:** Is 5xx < 0.1%?
- [ ] **Redis:** Is Memory Usage < 70%?

### 1.3. User Activity
- [ ] **Quota Blocks:** High rate (>20%) might indicate UX issue or aggressive pricing.
- [ ] **New Signups:** Are invites working?

## 2. Incident Triggers
If any check fails, refer to `INCIDENT_RESPONSE_PLAYBOOK_v1.md`.
