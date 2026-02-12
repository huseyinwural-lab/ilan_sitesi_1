# RCA: DEF-001 Tier Change Delay

**Defect:** Admin Tier Change reflects in DB but Rate Limit stays old for ~60s.
**Component:** Rate Limiter / Redis Cache.

## 1. Current Flow
1.  **Request:** `PATCH /admin/dealers/{id}/tier` updates DB `DealerPackage`.
2.  **Rate Limit Check:** Next request from Dealer calls `get_rate_limit_context`.
3.  **Cache Hit:** `get_rate_limit_context` checks Redis key `rl:context:{user_id}`.
4.  **Issue:** This key has a TTL of 60 seconds (optimization from P6).
5.  **Result:** The Limiter uses the *OLD* tier until TTL expires.

## 2. Root Cause
**Missing Event-Driven Invalidation:** The Admin Update endpoint does not explicitly clear the user's rate limit context cache. It relies on passive expiration.

## 3. Impact
-   **User:** Pays for Premium, still blocked for 1 minute.
-   **Support:** "I upgraded but still can't post."
-   **Severity:** P1 (High) -> Elevated to P0 (Blocker) for Launch.
