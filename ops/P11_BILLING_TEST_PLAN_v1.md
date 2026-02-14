# P11 Billing Test Plan

**Document ID:** P11_BILLING_TEST_PLAN_v1  
**Date:** 2026-02-13  
**Status:** 📝 DRAFT  

---

## 1. Unit Tests
- **Mock Provider:** Verify `create_checkout_session` returns URL without calling external API.
- **Webhook Verifier:** Test signature validation logic (Valid vs Invalid keys).

## 2. Integration Tests (Stripe Test Mode)

### 2.1. Happy Path
1. Call `POST /checkout` for "Pro Plan".
2. Use Stripe Mock Card (4242...) to pay.
3. Verify Webhook received.
4. Verify DB: `UserSubscription.status` is `active`.
5. Verify Quota: `QuotaService.get_limit()` returns 50.

### 2.2. Renewal Failure
1. Simulate `invoice.payment_failed` webhook.
2. Verify DB: `UserSubscription.status` is `past_due`.
3. Verify Quota: Remains active (Grace period) or Restricted (Policy dependent).

### 2.3. Cancellation
1. Call `POST /portal` -> Simulate Cancel in Stripe.
2. Receive `customer.subscription.updated` (cancel_at_period_end=true).
3. Verify DB: Status `active`, but `cancel_at` set.
4. Fast forward time -> Receive `deleted` webhook -> Verify status `expired`.

## 3. Idempotency Test
- Replay the same `checkout.session.completed` webhook 3 times.
- **Expected:** Subscription extended only ONCE.
