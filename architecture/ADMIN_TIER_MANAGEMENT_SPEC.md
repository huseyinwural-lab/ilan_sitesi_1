# Admin Tier Management Spec

**Component:** Admin Panel

## 1. Feature: Change Dealer Tier
-   **UI:** Dropdown on Dealer Detail Page (`Standard`, `Premium`, `Enterprise`).
-   **Action:** Update `DealerPackage` link or Override.
    -   *Preferred:* Upgrade Dealer's Subscription to a Package of that Tier.
-   **Validation:** Prevent downgrading if Quota usage > New Tier Limit (Soft check or warn).

## 2. Feature: Temporary Override
-   **UI:** "Boost Limit" Button (e.g., +500 reqs for 1 hour).
-   **Backend:** Writes `rl:override:{id}` to Redis.
-   **Audit:** Log `ADMIN_LIMIT_OVERRIDE` event.

## 3. History
-   **Table:** `audit_logs`
-   **Filter:** `resource_type='dealer_tier'`
-   **Display:** Who changed it, When, Old -> New.
