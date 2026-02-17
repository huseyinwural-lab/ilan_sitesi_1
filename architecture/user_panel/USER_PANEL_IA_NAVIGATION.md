# User Panel Information Architecture (IA)

## 1. Navigation Structure

### 1.1. Global Bottom Bar (Mobile)
1.  **Home** (`/`): Discovery feed.
2.  **Search** (`/search`): Advanced filters.
3.  **Sell** (`/sell`): **Primary Action**. Leads to Listing Wizard.
4.  **Inbox** (`/messages`): Chat list.
5.  **My Account** (`/account`): Dashboard entry.

### 1.2. My Account (Dashboard) Hierarchy
*   **Overview**:
    *   Active Listings Summary
    *   Unread Messages Badge
    *   Total Views (Last 7 Days)
*   **My Listings** (`/account/listings`):
    *   Tabs: Active, Pending, Expired, Drafts.
    *   Actions: Edit, Boost, Delete.
*   **My Profile** (`/account/profile`):
    *   Edit Info.
    *   Verification Status (Phone/ID).
*   **Wallet & Plans** (`/account/wallet`):
    *   Current Plan.
    *   Payment Methods.
    *   Invoice History.
*   **Settings**:
    *   Language/Country.
    *   Notifications.
    *   Legal (GDPR).

## 2. Routing Map (URL Scheme)
*   `/dashboard`: Redirects to `/account`.
*   `/listing/create`: Step 1 of Wizard.
*   `/listing/create/step-2`: Details.
*   `/listing/create/step-3`: Media.
*   `/listing/create/success`: Success state.
*   `/store/{dealer_slug}`: Public dealer page.
