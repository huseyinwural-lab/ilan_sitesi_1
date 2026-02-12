# P7 Admin Tier Module Spec

**Component:** Admin Panel > User Management > Dealer Detail

## 1. UI Specifications
-   **Tier Selector:** Dropdown showing `STANDARD`, `PREMIUM`, `ENTERPRISE`.
-   **Current Usage:** Display "Limit: 300/min | Used (Avg): 45/min".
-   **Action:** "Save Changes" button (Requires confirmation modal).

## 2. Backend Logic (API)
-   **Endpoint:** `PATCH /api/admin/dealers/{id}/tier`
-   **Auth:** `super_admin` only.
-   **Validation:**
    -   Check if requested Tier exists in `DealerPackage` enum.
    -   Prevent downgrade if current usage > new limit (Soft Warning).

## 3. Redis Strategy (Critical)
-   Upon successful DB update of `DealerPackage`:
    -   **Action:** Invalidate User Context.
    -   **Command:** `DEL rl:context:{user_id}` (or rely on next request to re-fetch if not cached).
    -   **Command:** `DEL rl:listings:{old_tier}:{user_id}` (Reset counters to avoid phantom blocks).

## 4. Audit
-   Log event: `ADMIN_CHANGE_TIER`
-   Data: `admin_id`, `dealer_id`, `old_tier`, `new_tier`, `reason`.
