# Rate Limit Config Migration Plan

**Goal:** Move hardcoded limits (e.g., `limit=60`) from Python code to Environment Variables/Config Logic.

## Phase 1: Environment Variables (Immediate)
- Define variables in `.env`:
    - `RL_LISTING_CREATE="60/60"`
    - `RL_AUTH_LOGIN="20/60"`
    - `RL_CHECKOUT="10/600"`

## Phase 2: Code Refactor (P6)
- Modify `app/core/rate_limit.py`:
    - Accept `config_key` instead of raw `limit/window`.
    - Example: `RateLimiter(key="listing_create")`.
    - Logic: Look up key in `app.core.config.settings`.

## Phase 3: Dynamic Updates (P7)
- Store limits in Redis/DB (`rate_limit_configs` table).
- Admin Panel UI to update limits without restart.
- Rate Limiter reads from Redis cache (refresh every 1 min).

## Phase 4: Distributed State
- Replace in-memory `_rate_limit_store` with Redis backend (`redis-py` + Lua scripts).
- Necessary for multi-pod deployments.
