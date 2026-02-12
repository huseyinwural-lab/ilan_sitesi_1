# Rate Limiter Tier Integration Spec

**Component:** `RedisRateLimiter` update.

## 1. Context Resolution Flow
1.  **Incoming Request** -> Auth Middleware -> `request.user`.
2.  **User Context:**
    -   If `user.role == 'super_admin'` -> Tier `ADMIN`.
    -   If `user.dealer_id`:
        -   Fetch Active Subscription from Cache/DB.
        -   Get `package.tier`.
        -   Return Tier (e.g., `PREMIUM`).
    -   Else -> Tier `STANDARD`.
3.  **Fallback:** If no user -> Tier `ANONYMOUS`.

## 2. Key Format Update
**Old:** `rl:{scope}:{id}`
**New:** `rl:{scope}:{tier}:{id}`
-   *Example:* `rl:listings:PREMIUM:u-123`

## 3. Backward Compatibility
-   Feature Flag: `TIER_LIMIT_ENABLED` (Bool).
-   If False: Use hardcoded `60` limit and legacy key format.
-   If True: Use Tier Logic.

## 4. Test Scenarios
-   **Scenario A:** Premium Dealer sends 100 req/min -> Allowed.
-   **Scenario B:** Standard Dealer sends 100 req/min -> Blocked at 61.
-   **Scenario C:** User downgrades package (Premium -> Standard) -> Limit reduces immediately (next request).
