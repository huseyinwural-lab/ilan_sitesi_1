# P13 Listing Lifecycle Policy

**Document ID:** P13_LISTING_LIFECYCLE_POLICY_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  

---

## 1. Expiration Rule
Listings that have not been updated for **90 days** will be automatically marked as `expired`.

### 1.1. "Update" Definition
Any action that updates `last_activity_at`:
- Price change
- Description edit
- Image update
- Explicit "Renew" button click

### 1.2. Expiration Effect
- **Status:** Changed from `active` -> `expired`.
- **Search:** Removed from public search results immediately.
- **Quota:** Resource slot (`listing_active`) is **released**.
- **Showcase:** If active, `showcase_active` slot is also released.

---

## 2. Renew Policy
Users can reactivate an expired listing.

- **Action:** Click "Renew" (Yeniden Yayınla).
- **Effect:** 
  - Status -> `active`.
  - `expires_at` -> NOW() + 90 days.
  - **Quota Check:** Requires an available slot. (Revised decision: Since we released the slot on expiry, renew MUST consume a slot again to be fair).

---

## 3. Data Retention
- Expired listings are kept indefinitely (Soft Delete logic).
- Purpose: SEO history, User history, Analytics.

## 4. Notifications
- **T-7 Days:** Email warning "İlanınızın süresi dolmak üzere".
- **T-0:** Email "İlanınız yayından kaldırıldı".
