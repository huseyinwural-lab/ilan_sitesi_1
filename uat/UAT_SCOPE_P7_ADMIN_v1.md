
# UAT Scope: P7 Admin Panel (v1.0)

**Phase:** P7 (Final Polish & UAT)
**Environment:** Staging (Seeded)
**Executor:** QA / Product Owner

## 1. Included Scope
This UAT cycle focuses on verifying the **Admin Panel Functionality** with the recently seeded "Live-like" dataset.

### Functional Areas:
-   **Navigation:** New menu structure and naming (P7 Renaming).
-   **Member Management:** Separation of Individual vs Commercial views.
-   **Commercial Operations:** Tier viewing, Package assignment, and Subscription status.
-   **Dashboard:** Verification of charts and counters with real data.
-   **Content:** Moderation queue workflow.
-   **Billing:** Invoice listing and details.
-   **System:** Audit Logs and Feature Flags.

## 2. Excluded Scope
-   **End-User Frontend:** The public marketplace UI is out of scope.
-   **New Code:** No new feature development; only verification of existing logic.
-   **Performance Testing:** Load testing was completed in P6.

## 3. Pre-requisites
-   [x] Database Migration (Tier column) applied.
-   [x] Seed Data (20 Users, 10 Dealers, 40 Listings) populated.
-   [x] Admin User (`admin@platform.com`) credentials active.
