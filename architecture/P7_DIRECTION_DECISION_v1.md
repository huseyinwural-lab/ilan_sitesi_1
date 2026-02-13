# P7 Direction Decision v1

**Selected Path:** Search/Filter API v2 First.
**Status:** LOCKED

## 1. Rationale
-   **Data Foundation:** We have migrated to `listing_attributes` (Typed EAV) and Master Data. The legacy search logic (JSONB) is obsolete.
-   **User Value:** A fast, faceted search is the core value proposition of the marketplace. Admin UI polish is secondary to core functionality.
-   **Dependency:** The Admin "Listing Management" screen will also consume this Search API for filtering.

## 2. Scope
-   **In-Scope:** Public Search API (`GET /api/search`), Facet Generation, Pagination, Sorting.
-   **Out-of-Scope:** Frontend Components, Admin Dashboard Visual Polish.
