# Quota Enforcement Activation Plan

## 1. Policy
We must enforce limits *before* a listing transitions from `DRAFT` to `PENDING_MODERATION`.

### 1.1. Individual Users
*   **Limit**: 2 Active Listings per year (Rolling window).
*   **Action**: If limit reached, redirect to "Upgrade to Premium" or "Delete Old Listing".

### 1.2. Commercial Users (Dealers)
*   **Limit**: Based on Active Subscription Plan.
    *   Basic: 10 Listings.
    *   Pro: 50 Listings.
*   **Action**: If limit reached, block new listings until upgrade.

## 2. Implementation Logic
*   **Hook Point**: `ListingService.submit_listing()`.
*   **Check**:
    1.  Count `active` + `pending` listings for user.
    2.  Fetch User Quota (from `UserSubscription` or `DealerPackage`).
    3.  If Count >= Quota -> Raise `402 Payment Required`.

## 3. Expiry
*   **Auto-Expire**: Job runs daily at 00:00. Sets `status='expired'` for listings older than 30 days (Individual) or Plan Duration (Commercial).
