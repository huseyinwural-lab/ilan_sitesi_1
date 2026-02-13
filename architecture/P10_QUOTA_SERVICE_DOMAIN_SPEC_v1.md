# P10 Quota Service Domain Specification

**Document ID:** P10_QUOTA_SERVICE_DOMAIN_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  

---

## 1. Core Logic
The Quota Service acts as the **Gatekeeper** for resource consumption. It answers one question: *"Can User X perform Action Y?"*

### 1.1. Plan Resolution Logic
When checking quota, we first determine the user's active plan:
1. **Active Subscription:** If `user_subscriptions` has an active record -> Use Plan Limits.
2. **Individual (No Sub):** Fallback to **Global Free Tier** (Default: 3 Active Listings).

### 1.2. Resource Types
- `listing_active`: Count of currently active listings.
- `showcase_active`: Count of listings with `is_showcase=True`.

---

## 2. API Contract

### 2.1. `check_quota(user_id, resource_type)`
- **Returns:** `True` if usage < limit, else `False`.
- **Side Effect:** None (Read-only).

### 2.2. `consume_quota(user_id, resource_type)`
- **Action:** Increments `used` count in `quota_usage`.
- **Validation:** Re-checks limit inside transaction (Race condition protection).
- **Raises:** `QuotaExceededException` if limit reached.

### 2.3. `release_quota(user_id, resource_type)`
- **Action:** Decrements `used` count.
- **Trigger:** Listing deletion, expiration, or status change (e.g., active -> pending).

---

## 3. Concurrency Safety
- **Locking:** `SELECT ... FOR UPDATE` on `quota_usage` row during consumption.
- **Consistency:** Quota usage table is the source of truth for *limits*, but periodic reconciliation jobs (P11) will ensure it matches `COUNT(*)` from listings.

---

## 4. Edge Cases
- **Plan Downgrade:** If User moves from Pro (50) to Basic (10) but has 40 listings:
  - `check_quota` returns `False` immediately.
  - Existing listings remain active (grandfathered until expiry).
- **Subscription Expiry:** Treated as "No Plan" -> Fallback to Free Limit.
