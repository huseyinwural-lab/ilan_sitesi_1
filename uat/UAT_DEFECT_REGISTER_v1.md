# UAT Defect Register

**Status:** OPEN

| Defect ID | Severity | Description | Component | Status | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | **P1** | **Tier Change Delay:** Updating Tier in Admin UI reflects in DB immediately, but Redis Rate Limit context takes > 60s to update. | `RedisRateLimiter` / `commercial_routes` | **OPEN** | Backend Dev |

**Triage Notes:**
-   *Impact:* User might still be throttled for 1 minute after paying for upgrade.
-   *Root Cause:* Redis context caching `rl:context:{user_id}` TTL is likely 60s. Need immediate invalidation on Admin Action.
-   *Decision:* Must Fix for Go-Live.
