# P6 Rate Limiting Architecture: Distributed Strategy

## 1. Decision: Redis-Backed Centralized Limiter
**Verdict:** Use Redis as the shared state store.
**Rationale:**
- **Accuracy:** Enforces global limits across all application pods.
- **Performance:** Redis atomic operations (Lua scripts) ensure low latency (<1ms).
- **Features:** Supports "Sliding Window" which is fairer than "Fixed Window".

## 2. Architecture
- **Middleware:** `FastAPI-Limiter` or Custom Middleware.
- **Storage:** Redis Cluster / Managed Redis.
- **Key Schema:** `rl:{namespace}:{identifier}`.
- **Fallback:** If Redis is down -> Fail Open (Allow traffic) + Log Error (Prevent outage).

## 3. Migration Plan
1.  **Infrastructure:** Provision Redis (e.g., AWS ElastiCache / Render Redis).
2.  **Code:** Replace `_rate_limit_store` (Dict) with `redis.incr` logic.
3.  **Config:** Move hardcoded limits to Redis Hash or Config File watched by app.
4.  **Rollout:** Deploy alongside app; toggle via `RATE_LIMIT_BACKEND=redis`.

## 4. Alternative Considered: Gateway Limiting (Nginx/Cloudflare)
- **Pros:** Faster (blocks at edge).
- **Cons:** Less granular. Harder to implement logic like "Tier 1 vs Tier 2" based on JWT claims.
- **Conclusion:** Keep Gateway for DDoS protection (Layer 3/4), use App/Redis for Business Logic Limiting (Layer 7).
