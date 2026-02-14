# P12 Self Service Plan Management

**Document ID:** P12_SELF_SERVICE_PLAN_MANAGEMENT_v1  
**Date:** 2026-02-13  
**Status:** ✅ COMPLETED  

---

## 1. Features
- **View Plan:** `GET /billing/subscription` returns full details.
- **Buy Plan:** `POST /billing/checkout` redirects to Stripe.
- **Manage/Cancel:** `POST /billing/portal` redirects to Stripe Portal.

## 2. Integration Status
- **Frontend:** `Billing.js` and `Plans.js` integrated with API.
- **Stripe:** Checkout and Portal sessions functional (Test Mode).
- **Webhooks:** Quota unlock verified.

## 3. Quota Behavior
- **Upgrade:** Instant unlock.
- **Cancel:** Active until period end.
- **Expire:** Fallback to Free limit (verified by `test_billing_integration.py`).

**Ready for Production Keys.**
