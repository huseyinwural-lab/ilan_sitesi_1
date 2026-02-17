# Search Caching Strategy v1

## 1. Strategy: "Search Result Page" Caching
Since search queries follow a "Power Law" (few popular queries = most traffic), we cache the SERP (Search Engine Result Page).

## 2. Key Selection (Cache Key)
`search:{country}:{segment}:{transaction}:{type}:{city}:{sort}:{page}`
*   Example: `search:de:konut:satilik:daire:berlin:newest:1`

## 3. Policy
*   **TTL (Time To Live)**:
    *   Popular Cities (Berlin, Istanbul): 5 minutes.
    *   Long-tail: 1 hour.
    *   Facets: 24 hours.
*   **Invalidation**:
    *   On `Listing.create`: Do nothing (Wait for TTL, or soft expire).
    *   On `Listing.sold/deleted`: Remove from cache immediately if in top 20? No, let TTL expire. Cost of stale data < Cost of complex invalidation.

## 4. Implementation (Redis)
*   **Store**: JSON string of `SearchResponse`.
*   **Compression**: GZIP (Text data compresses well).
*   **Layer**: `SearchService` decorator.
