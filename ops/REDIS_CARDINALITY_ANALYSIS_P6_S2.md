# Redis Cardinality Analysis (P6 S2)

**Risk Assessment:** High Cardinality due to User-based keys.

## 1. Estimation
-   **Active Users (Daily):** 5,000
-   **Scopes:** ~5 (Listings, Auth, etc.)
-   **Total Keys:** 25,000 keys.
-   **Hash Size:** ~100 bytes.
-   **Total Memory:** ~2.5 MB.

## 2. Conclusion
-   Memory impact is negligible compared to 4GB capacity.
-   Even with 1M users -> ~500MB.
-   **Risk:** Low.

## 3. Safety Net
-   **TTL:** Keys expire after 60s. This keeps the active set size proportional to *concurrent* users, not total users.
-   **Eviction:** `volatile-lru` active.
