# P12 Plan Transition Flow

**Document ID:** P12_PLAN_TRANSITION_FLOW_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Upgrade Flow
1. **Trigger:** User clicks "Upgrade" on Billing Page or blocked creation.
2. **Action:** `POST /api/v1/billing/checkout` -> Stripe.
3. **Success:** Return to Dashboard -> Toast "Plan upgraded".
4. **Effect:** Limit increased immediately via Webhook.

## 2. Downgrade/Cancel Flow
1. **Trigger:** User clicks "Manage Billing" -> Stripe Portal -> Cancel Subscription.
2. **Webhook:** `customer.subscription.updated` (cancel_at_period_end=true).
3. **UI State:** Status badge changes to "Cancelling" (Active until end date).
4. **Expiry:** When period ends -> Webhook `deleted` -> Status "Expired".
5. **Effect:** Quota reverts to Free (3).
   - **Legacy Data:** Existing listings > 3 are NOT deleted (soft policy) but new creations blocked.

## 3. UX Messages
- **Free:** "You have 3 free listings."
- **Pro:** "You have 50 listings. Thank you for your business!"
- **Past Due:** "Payment failed. Please update card to keep listings active."
