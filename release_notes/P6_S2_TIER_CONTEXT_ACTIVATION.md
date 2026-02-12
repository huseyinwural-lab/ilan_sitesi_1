
# P6 Sprint 2: Tier Context Activation

**Feature:** Dynamic Rate Limit Context

## 1. Logic Update
-   **Resolver:** `get_rate_limit_context` (New Dependency)
-   **Chain:**
    1.  `request.user` -> Check Role (`super_admin` -> ADMIN)
    2.  `user.dealer_id` -> `DealerSubscription` -> `DealerPackage.tier`.
    3.  Default -> STANDARD.

## 2. Key Format
-   `rl:{scope}:{tier}:{user_id}`
-   Example: `rl:listings:PREMIUM:u-123`

## 3. Configuration
-   `TIER_LIMIT_ENABLED = True` (Feature Flag).
-   `RL_STANDARD = 60/min`
-   `RL_PREMIUM = 300/min`

## 4. Verification
-   **Unit Tests:** Added to `test_p6_s2_tier_limits.py`.
    -   Premium user allows 70 req/min.
    -   Standard user blocks at 61 req/min.

**Status:** ACTIVE (Code Ready)
