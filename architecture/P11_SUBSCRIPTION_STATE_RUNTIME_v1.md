# P11 Subscription State Runtime

**Document ID:** P11_SUBSCRIPTION_STATE_RUNTIME_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. State Mapping

| Stripe Status | Internal Status | Quota Behavior |
|---|---|---|
| `active` | `active` | Full Plan Limit |
| `trialing` | `active` | Full Plan Limit |
| `past_due` | `past_due` | Full Plan Limit (Grace Period) |
| `canceled` | `active` | Active until period end, then Expired |
| `unpaid` | `expired` | Free Fallback |
| `incomplete` | `pending` | Blocked / Free Fallback |

## 2. Expiry Logic
- **Runtime:** `QuotaService` checks `UserSubscription.end_at`.
- **Background:** Daily job scans for `end_at < NOW()` and updates status to `expired` if no webhook received.

## 3. Fallback
If `status != active` (and grace period over), `QuotaService.get_limits()` returns default Free tier (3 listings).
