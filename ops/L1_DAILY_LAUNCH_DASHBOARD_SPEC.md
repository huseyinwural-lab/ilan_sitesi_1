# Daily Launch Dashboard Spec

## 1. Supply Metrics (Daily)
*   **New Listings**: Count of `listings` created in last 24h.
*   **Active Listings**: Total count with `status='active'`.
*   **Dealer Signups**: Count of new `dealers`.
*   **Listings per Dealer**: Avg active listings per dealer account.

## 2. Demand Metrics (Daily)
*   **Search Volume**: Count of `search_performed` events.
*   **Detail Views**: Count of `listing_viewed` events.
*   **Reveals (Leads)**: Count of `listing_contact_clicked`.
*   **Conversion Rate**: `Reveals / Detail Views`.

## 3. Operations Metrics
*   **Pending Moderation**: Count of listings waiting > 4 hours.
*   **Reported Listings**: Count of user reports.
*   **5xx Errors**: Count of server errors.

## 4. Implementation
*   **Tool**: Admin Panel > Dashboard (P25 Hypercare View expanded).
*   **Alerts**: Slack message if `New Listings < 10` or `5xx > 0`.
