# Production Readiness Audit

**Document ID:** PRODUCTION_READINESS_AUDIT_v1  
**Date:** 2026-02-13  
**Status:** 🟡 IN PROGRESS  

---

## 1. Stripe & Payment Configuration
- [ ] **Live Keys:** Configured in Production Environment (`STRIPE_SECRET_KEY` starts with `sk_live_`).
- [ ] **Webhook Endpoint:** Configured in Stripe Dashboard (`https://api.platform.com/api/v1/billing/webhook`).
- [ ] **Webhook Secret:** Synced between Stripe Dashboard and Backend Env (`STRIPE_WEBHOOK_SECRET`).
- [ ] **Product Mapping:** Production Product/Price IDs mapped correctly in `billing_routes.py` (or DB config).

## 2. Infrastructure & Security
- [x] **Rate Limiting:** `60 req/min` active on Search API.
- [ ] **SSL:** Valid certificate for `api.platform.com` and `platform.com`.
- [ ] **HSTS:** Enabled on Nginx/Ingress.
- [ ] **Database Backup:** Daily snapshots + WAL archiving configured (Point-in-time recovery).

## 3. Critical Flow Verification (Smoke Test)
*These must be verified manually in the Live environment before public announcement.*

1. **Sign Up:** Create a new user.
2. **Quota Check:** Create 3 listings -> 4th blocked (Free Tier).
3. **Upgrade:** Purchase "Basic Plan" (Real card, small amount/refund).
4. **Unlock:** Create 4th listing -> Success.
5. **Cancel:** Cancel subscription -> Status updates.

## 4. Monitoring Baseline
- **Alerts:**
  - `quota_block_rate > 10%` (Investigate abuse or UX friction).
  - `payment_failure_rate > 5%`.
  - `webhook_error_rate > 1%`.

---

**Next Step:** Implement Monitoring Alerts.
