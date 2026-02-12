# Rate Limit v2 Migration Roadmap (Memory -> Redis)

## Phase 1: Feature Flag & Shadow Mode
-   **Config:** `RATE_LIMIT_BACKEND = "memory"` (Default).
-   **Action:** Implement `RedisRateLimiter`.
-   **Shadow Mode:**
    -   Incoming Request -> Check Memory Limiter (Enforce).
    -   Async/Background -> Increment Redis Counter (Log only).
    -   Compare counts in logs.

## Phase 2: Log-Only Validation
-   **Config:** `RATE_LIMIT_BACKEND = "redis"`, `RATE_LIMIT_ENFORCE = False`.
-   **Action:**
    -   Switch main logic to Redis.
    -   If Limit Exceeded -> Log "Would have blocked" -> Allow request.
    -   Monitor latency impact of Redis calls.

## Phase 3: Cutover (Enforcement)
-   **Config:** `RATE_LIMIT_ENFORCE = True`.
-   **Action:** Full Distributed Rate Limiting active.
-   **Rollback:** Keep `MemoryRateLimiter` code as fallback.

## Phase 4: Cleanup
-   Remove `_rate_limit_store` (Memory Dict) code.
-   Remove Shadow Mode logic.
