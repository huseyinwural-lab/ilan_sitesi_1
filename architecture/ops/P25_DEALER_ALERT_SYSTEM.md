# P25: Dealer Alert System

## 1. Trigger: Low Performance
*   **Condition**: `Active Listings > 10` AND `Leads (Last 7d) == 0`.
*   **Action**: Email "Your listings are not getting attention. Try boosting or checking prices."

## 2. Trigger: Quota Exhaustion
*   **Condition**: `Listing Count == Quota`.
*   **Action**: Email "You reached your limit. Upgrade to Pro for 50 more listings."

## 3. Trigger: Expiring Boosts
*   **Condition**: `Showcase Expires In < 24h`.
*   **Action**: Email/Push "Your showcase is ending. Renew now to keep top spot."
