# P7 Scope Lock: Final Polish & Admin UI

**Start Date:** 2026-03-01
**Duration:** 2 Weeks

## 1. In-Scope Deliverables
### A. Admin Panel (Frontend + API)
-   **Tier Management:** View/Edit Dealer Tiers.
-   **Rate Limit Monitor:** Live view of "Blocked Requests" (Metric proxy).
-   **Health Dashboard:** Redis/DB/Job status indicators.
-   **Abuse Watch:** List of "High Risk" IPs/Users.

### B. System Health
-   **Logs UI:** Simple log viewer for specific `request_id` (Admin only).
-   **Archival:** Move old logs/invoices to "Archive" tables or S3 logic.

## 2. Out-of-Scope
-   **New Business Features:** No new selling models.
-   **Mobile App:** Admin is Web-only.
-   **Complex Analytics:** BI tool integration deferred.

## 3. Success Criteria
-   Admin can change a user's Tier without SQL access.
-   Support can debug a "Why blocked?" ticket using Admin Panel.
