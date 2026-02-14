# P11 Payment Gateway Scope Kickoff

**Document ID:** P11_PAYMENT_GATEWAY_SCOPE_v1  
**Date:** 2026-02-13  
**Status:** 🚀 ACTIVE  

---

## 1. Objective
Enable automated revenue collection by integrating a Payment Gateway to sell Subscriptions (Dealer Plans) and One-off Credits (Individual Listings).

## 2. In Scope (MVP)
### 2.1. Subscription Management
- **Purchase:** Checkout session for Monthly/Yearly plans.
- **Renewal:** Automated recurring billing via Provider.
- **Cancellation:** User-initiated cancel at period end.
- **State Sync:** Webhook-driven status updates (Active -> Past Due -> Canceled).

### 2.2. Billing Records
- **Invoices:** Store PDF URL and transaction history.
- **Payment Methods:** Tokenized card storage (Off-DB, via Provider).

### 2.3. Quota Unlock
- Successful payment event -> Update `user_subscriptions` -> `QuotaService` sees active plan.

## 3. Out of Scope (Phase 1)
- **Disputes/Chargebacks:** Managed manually via Provider Dashboard.
- **Proration:** No complex upgrade/downgrade math (Cancel then Subscribe New).
- **Multi-currency checkout:** Prices fixed per country plan.

## 4. Acceptance Criteria
- User can buy a plan via Credit Card.
- `QuotaService` reflects the new limit immediately after Webhook processing.
- Failed renewal downgrades user to Free tier automatically.
