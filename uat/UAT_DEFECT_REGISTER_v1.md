# UAT Defect Register

**Status:** UPDATED

| Defect ID | Severity | Description | Component | Status | Owner |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-001** | **P0** | **Tier Change Delay:** Updating Tier in Admin UI reflects in DB immediately, but Redis Rate Limit context takes > 60s to update. | `RedisRateLimiter` / `admin_routes` | **CLOSED** | Backend Dev |

**Resolution:**
-   Implemented `invalidate_context` in `RedisRateLimiter`.
-   Admin `PATCH /tier` endpoint calls invalidation synchronously.
-   Regression Test (`test_fix_def001.py`) verified flow.
-   **Ready for Retest.**
