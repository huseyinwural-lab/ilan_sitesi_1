# Rate Limit v2 Technical Design

**Pattern:** Hierarchical Dynamic Limits
**Backend:** Redis (Lua Scripts)

## 1. Hierarchy & Precedence
When a request arrives, the Limit is determined by the specific `key`:

1.  **Override Key:** `rl:override:{user_id}` (Manual Admin set).
    -   *If exists, use this limit.*
2.  **Tier Key:** Derived from User Role / Dealer Package.
    -   `Premium`: 300/min.
    -   `Standard`: 60/min.
3.  **Default Key:** Code default (fallback).

## 2. Key Format
```text
rl:{namespace}:{tier_id}:{identifier}:{window}
```
*Example:* `rl:listings:premium_package_v1:u-123:60`

## 3. Logic Flow
1.  **Auth Middleware:** Resolves `User`.
2.  **Context Builder:** Fetches `DealerSubscription` -> `DealerPackage` -> `Tier`.
3.  **Rate Limiter:**
    -   Input: `user_id`, `tier_limit`.
    -   Check Redis.
    -   Block if exceeded.

## 4. Segment Explosion Control
-   **Risk:** Creating a unique limit rule for every user.
-   **Control:** Map users to a finite set of Tiers (Basic, Pro, Ent, Admin). Do not allow custom limits per user unless via Override Key (Expiring).
