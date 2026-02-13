# P9 Redis Implementation Spec

**Document ID:** P9_REDIS_IMPLEMENTATION_SPEC_v1  
**Date:** 2026-02-13  
**Status:** 🏗️ ARCHITECTURE  

---

## 1. Objective
Implement a caching layer to serve repeated search queries from memory, reducing DB load and P50 latency.

## 2. Key Design

### 2.1. Cache Key Format
Query parameters must be canonicalized to ensure hit rate.

**Format:** `search:v2:{sha256_hash}`
**Payload for Hash:** 
```json
{
  "q": "bmw",
  "category": "cars", 
  "attrs": {"brand": ["bmw"], "year": {"min": 2020}},
  "sort": "price_asc",
  "page": 1
}
```
*Keys are sorted alphabetically before hashing.*

### 2.2. Content
- **Type:** JSON String (Gzipped if > 10KB).
- **Data:** Full API Response (Items + Facets + Pagination).

### 2.3. TTL Strategy
- **Search Results:** 60 seconds (Soft TTL).
- **Rationale:** Listing inventory changes frequently; 1 minute is a good balance between freshness and offloading bursts.

## 3. Class Structure

```python
class RedisCache:
    def __init__(self, redis_url):
        self.redis = redis.from_url(redis_url)

    async def get(self, key):
        # return decompressed json
        pass

    async def set(self, key, value, ttl=60):
        # compress and store
        pass

def cache_key_builder(func, *args, **kwargs):
    # Sort params -> Hash
    pass
```

## 4. Rollout
- **Feature Flag:** `ENABLE_REDIS_CACHE=True` (Env var).
- **Error Handling:** If Redis fails, log error and return fresh DB result (Fail open).
