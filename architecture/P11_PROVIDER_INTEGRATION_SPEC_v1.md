# P11 Provider Integration Spec

**Document ID:** P11_PROVIDER_INTEGRATION_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Provider Choice
**Stripe** (Primary) / **Iyzico** (Secondary for TR local).
*For MVP, we define a generic Interface, implemented by `StripeProvider`.*

## 2. Abstraction Layer
`app.services.payment.base.PaymentProvider`

- `create_customer(user)`
- `create_checkout_session(customer_id, plan_id, success_url, cancel_url)`
- `get_portal_url(customer_id)` (For self-service management)
- `verify_webhook(payload, signature)`

## 3. Webhook Strategy (Source of Truth)

### 3.1. Critical Events
| Provider Event | Internal Action |
|---|---|
| `checkout.session.completed` | Activate `UserSubscription`. Unlock Quota. |
| `invoice.payment_succeeded` | Extend `current_period_end`. Record `Payment`. |
| `invoice.payment_failed` | Set Subscription `status='past_due'`. Notify User. |
| `customer.subscription.deleted` | Set Subscription `status='expired'`. Lock Quota. |

### 3.2. Idempotency
- Store `processed_event_ids` in DB or Redis (TTL 24h).
- If event ID exists, return 200 OK immediately without processing.

### 3.3. Security
- Verify cryptographic signature of webhook payload.
- Reject requests with timestamp > 5 mins old (Replay protection).
