# P9 Redis Caching Strategy

**Document ID:** P9_REDIS_CACHING_STRATEGY_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Scope
Cache expensive "Read" operations that have high frequency and low tolerance for latency.

## 2. Cache Keys

### 2.1. Search Results
**Pattern:** `search:v2:{hash}`
- `hash`: SHA256 of sorted query params (e.g., `category=cars&sort=price_asc`).
- **TTL:** 60 seconds (Short enough to reflect new listings, long enough to absorb bursts).
- **Content:** Full JSON response (Items + Facets).

### 2.2. Facet Aggregation (Separate?)
**Decision:** NO. Caching the full search response is simpler and prevents inconsistency between items and facets.

### 2.3. Detail Page
**Pattern:** `listing:v2:{uuid}`
- **TTL:** 5 minutes.
- **Invalidation:** On `UPDATE/DELETE` listing event.

## 3. Implementation
- **Middleware/Decorator:** `@cache(ttl=60)` decorator on FastAPI route handler.
- **Serialization:** Fast JSON (e.g., `orjson`) serialization before storing in Redis.
- **Compression:** GZIP if payload > 10KB (Facet data can be large).

## 4. Fallback
If Redis is down, proceed to DB (Graceful degradation). Log error but don't fail request.
