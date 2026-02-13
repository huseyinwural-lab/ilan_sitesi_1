# Redis Cache Metrics Plan

**Document ID:** REDIS_CACHE_METRICS_PLAN_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ PLANNED  

---

## 1. Metrics to Collect
Since we don't have a full Prometheus setup, we will log metrics to `stdout` (which is captured by CloudWatch/Datadog in prod) and expose a simple `/api/admin/metrics` endpoint.

### 1.1. Counters
- `cache.hit`: Count of requests served from Redis.
- `cache.miss`: Count of requests hitting DB.
- `cache.error`: Redis connection failures.

### 1.2. Histograms
- `db.latency`: Time taken when cache miss.
- `cache.latency`: Time taken to fetch from Redis.

## 2. Implementation
Add a middleware or update `RedisCache` class to increment local counters.

```python
# Simple in-memory counter for Beta
METRICS = {
    "hits": 0,
    "misses": 0
}
```

## 3. Visualization
For the Beta phase, we will check these metrics via:
`GET /api/admin/cache/stats`

---

**Next Step:** Implement `Cache Invalidation Policy`.
