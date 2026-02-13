# RC: P7 Admin API MasterData & Search v2

**Status:** READY FOR HANDOFF
**Date:** 2026-03-20

## 1. Components
### A. Admin MasterData API
-   **Base:** `/api/v1/admin/master-data`
-   **Features:** Attributes CRUD, Options CRUD, Category Binding.
-   **Security:** Strict RBAC (Country Admin vs Super Admin).

### B. Search API v2
-   **Base:** `/api/v2/search`
-   **Features:** Faceted Search, Typed Filtering, Category Inheritance.
-   **Performance:** p95 < 150ms targeted.

## 2. Integration Contract
-   **Admin updates** to `is_filterable` reflect immediately in **Search Facets**.
-   **Admin updates** to `label` reflect immediately in **Search Facets** (Subject to 5m TTL if cached).

## 3. Deployment
-   **Breaking Changes:** None. V2 is parallel to V1 (if exists).
-   **Rollback:** Standard Revert.
