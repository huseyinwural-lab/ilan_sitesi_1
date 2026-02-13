# P10 Quota Enforcement Spec

**Document ID:** P10_QUOTA_ENFORCEMENT_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Enforcement Flow (Create Listing)

When `POST /api/v1/listings` is called:

1.  **Identify User Segment:**
    - Is `user.role == 'dealer'`?
        - **Yes:** Check Active Subscription.
        - **No:** Check Individual Limit (Free) OR Pre-purchased Credits.

2.  **Check Quota:**
    - `usage = quota_service.get_usage(user_id)`
    - `limit = quota_service.get_limit(user_id)`
    - **Logic:** `if usage >= limit: raise QuotaExceededError`

3.  **Reserve Slot (Optimistic Lock):**
    - `quota_service.increment_usage(user_id)` inside transaction.

4.  **Create Listing:**
    - Insert into `listings`.

5.  **Commit/Rollback:**
    - If Listing insert fails -> Decrement usage.

---

## 2. Hard vs Soft Limits
- **Hard Limit:** Listing Creation. User CANNOT create more than limit.
- **Soft Limit:** Views/Leads. (We don't block access, but maybe upsell).

## 3. Limit Calculation Logic
```python
def get_limit(user):
    if user.is_individual:
        return FREE_LIMIT + user.purchased_extra_slots
    elif user.subscription.is_active:
        return user.subscription.plan.limits['listing']
    else:
        return 0 (Or fallback to free limit)
```

## 4. Edge Cases
- **Subscription Expiry:** Scheduled job runs daily. If expired -> Set `status=expired` -> Deactivate listings > Limit.
- **Downgrade:** User switches from Pro (50) to Basic (10) but has 40 listings.
  - **Policy:** Keep 10 newest active, deactivate 30. Notify user.
