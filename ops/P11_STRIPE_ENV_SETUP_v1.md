# P11 Stripe Environment Setup

**Document ID:** P11_STRIPE_ENV_SETUP_v1  
**Date:** 2026-02-13  
**Status:** ✅ COMPLETED (Simulated)  

---

## 1. Credentials
*Mock credentials for development environment. In production, these will be injected via Secret Manager.*

| Key | Value (Dev) | Description |
|---|---|---|
| `STRIPE_PUBLISHABLE_KEY` | `pk_test_mock_12345` | Frontend JS |
| `STRIPE_SECRET_KEY` | `sk_test_mock_12345` | Backend API |
| `STRIPE_WEBHOOK_SECRET` | `whsec_mock_12345` | Webhook verification |

## 2. Product Mapping
Mapping between internal Plan Codes and Stripe Price IDs.

| Plan Code | Stripe Product ID | Stripe Price ID (Monthly) |
|---|---|---|
| `TR_DEALER_BASIC` | `prod_basic_tr` | `price_basic_tr_mo` |
| `TR_DEALER_PRO` | `prod_pro_tr` | `price_pro_tr_mo` |
| `TR_DEALER_ENTERPRISE` | `prod_ent_tr` | `price_ent_tr_mo` |

## 3. Webhook Configuration
- **URL:** `https://api.platform.com/api/v1/billing/webhook`
- **Events Subscribed:**
  - `checkout.session.completed`
  - `invoice.payment_succeeded`
  - `invoice.payment_failed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`

---

**Next Step:** Database Schema Implementation.
