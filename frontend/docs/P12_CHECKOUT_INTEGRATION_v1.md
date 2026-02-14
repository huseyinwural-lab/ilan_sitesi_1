# P12 Checkout Integration

**Document ID:** P12_CHECKOUT_INTEGRATION_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Flow
1. **User Action:** Clicks "Planı Yükselt" or "Satın Al".
2. **API Call:** `POST /api/v1/billing/checkout` with `{ plan_code }`.
3. **Response:** `{ url: "https://checkout.stripe.com/..." }`.
4. **Redirect:** `window.location.href = url`.
5. **Return:** Stripe redirects back to `/admin/billing?status=success`.

## 2. Components
### 2.1. `PlansPage`
- Lists available plans (Basic, Pro, Enterprise).
- Displays price, limits, and features.
- "Select" button triggers API call.

### 2.2. `BillingResult` (Toast/Modal)
- Checks URL query params on load.
- If `status=success`: Show "Subscription Active" confetti/toast.
- If `status=cancel`: Show "Payment Cancelled" warning.

## 3. Error Handling
- **Network Error:** "Payment service unavailable".
- **403 Forbidden:** "You cannot downgrade at this time" (if applicable).
- **502 Bad Gateway:** Stripe connection error.
