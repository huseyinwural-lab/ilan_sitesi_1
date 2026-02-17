# Search Cache Activation Plan

## 1. Scope
Activate caching for high-volume search queries to protect the database during launch spikes.

## 2. Configuration (Redis)
*   **Host**: Localhost (MVP) / Managed Redis (Prod).
*   **Memory Limit**: 1GB (Eviction policy: `allkeys-lru`).

## 3. Caching Rules
*   **Home Page Feed**: Cache `search_real_estate(country='DE', sort='newest')` for 5 mins.
*   **City Landing Pages**: Cache `Berlin`, `Munich`, `Istanbul` queries for 5 mins.
*   **Filters**: Queries with > 2 filters are NOT cached initially (Long tail).

## 4. Invalidation
*   **Passive**: rely on TTL (5 min).
*   **Active**: Not implemented for V1 (Acceptable staleness).
