# Dealer Dashboard Information Architecture

## 1. Overview
A specialized dashboard for high-volume sellers to manage inventory and leads.

## 2. Modules

### 2.1. Key Metrics (Header)
*   **Active Listings**: 45 / 50 (Limit)
*   **Showcase Remaining**: 2 / 5
*   **Total Views (30d)**: 12,500
*   **Total Leads (30d)**: 140

### 2.2. Listing Management (Table)
*   **Bulk Actions**: Select All -> Deactivate / Renew / Boost.
*   **Columns**: Photo, Title, Price, Views, Messages, Calls, Status, Expires In.
*   **Filters**: Active, Expired, Low Performance.

### 2.3. Lead Inbox (Mini CRM)
*   Consolidated view of Messages + Reveal Events.
*   **Status**: New, Contacted, Closed.

## 3. Navigation
*   `/dealer/dashboard` (Home)
*   `/dealer/inventory`
*   `/dealer/leads`
*   `/dealer/settings` (Company Info)
