# P11 API Surface

**Document ID:** P11_API_SURFACE_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Public Billing Endpoints (`/api/v1/billing`)

### `POST /checkout`
Create a session to buy a plan.
- **Input:** `plan_code` (e.g., "TR_DEALER_PRO")
- **Output:** `{"url": "https://checkout.stripe.com/..."}`
- **Logic:** 
  1. Get/Create Provider Customer for User.
  2. Resolve Price ID from Plan Code.
  3. Generate Session URL.

### `POST /portal`
Generate a link to the self-service billing portal (Update card, Cancel).
- **Input:** None.
- **Output:** `{"url": "..."}`

### `POST /webhook`
Public endpoint for Provider callbacks.
- **Input:** Raw Body + Header Signature.
- **Logic:** Verify -> Parse -> Dispatch to Handler.

---

## 2. Internal/Admin Endpoints (`/api/v1/admin/billing`)

### `GET /subscriptions`
List all subscriptions.
- **Filters:** Status, Plan, User.

### `POST /subscriptions/{id}/cancel`
Force cancel a subscription (Admin override).

---

## 3. Data Flow
1. **User** -> `POST /checkout` -> **API** -> `Stripe Session`
2. **User** -> Pay at Stripe -> **Stripe**
3. **Stripe** -> `POST /webhook` -> **API** -> Update DB -> Unlock Quota.
4. **User** -> Redirect to Success Page -> See upgraded limits.
