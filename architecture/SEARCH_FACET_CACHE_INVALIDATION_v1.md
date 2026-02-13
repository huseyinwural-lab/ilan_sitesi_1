# Search Facet Cache Invalidation v1

**Strategy:** TTL + Event Driven.

## 1. Caching Layer
-   Cache Key: `search:{category_id}:{lang}:{hash(filters)}`.
-   TTL: 5 minutes (Short lived).

## 2. Invalidation Events
-   **Immediate:** Admin updates Master Data (Option Label change). -> Clear ALL search cache?
    -   *Decision:* Too expensive. Rely on TTL (5 min staleness acceptable for label updates).
-   **Immediate:** New Listing Published.
    -   *Decision:* No invalidation. New listing appears in 5 mins.

## 3. Manual Purge
-   Admin Button: "Clear Search Cache".
