# Legacy Limiter Removal Plan

**Target:** T+24h after Cutover
**PR:** `chore/remove-legacy-limiter`

## 1. Code Cleanup
-   Delete `app/core/rate_limit.py` (Memory implementation).
-   Remove `_rate_limit_store` dictionary.
-   Remove `clean_expired_entries` background task (if any).

## 2. Dependency Impact
-   Verify `RateLimiter` dependency injection in `commercial_routes.py` and `server.py` now points exclusively to `RedisRateLimiter`.
-   Remove `RATE_LIMIT_BACKEND` config toggle (Only Redis supported).

## 3. Verification
-   **Unit Tests:** Update tests to mock Redis instead of clearing memory dict.
-   **Integration:** Verify `429` still returns correct headers.

## 4. Risk
-   **Risk:** If Redis fails, we have no "Local Memory" fallback anymore.
-   **Mitigation:** We rely on "Fail-Open" (Allow Traffic) strategy as agreed in P6 Arch.
