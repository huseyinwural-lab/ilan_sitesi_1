# Task: DEF-001 Fix Implementation

**Target:** `app/routers/admin_routes.py` (or where PATCH tier lives).

## Steps
1.  **Refactor:** Ensure `RedisRateLimiter` or a helper `RateLimitService` exposes an `invalidate_context(user_id)` method.
2.  **Integrate:** In the PATCH endpoint:
    -   Perform DB Update.
    -   Commit DB.
    -   Call `invalidate_context(user_id)`.
    -   Return 200 OK.
3.  **Log:** Add structlog event `event="cache_invalidated"`.

## Unit Test
-   Mock Redis.
-   Call Update Tier.
-   Assert `redis.delete("rl:context:{id}")` was called.
