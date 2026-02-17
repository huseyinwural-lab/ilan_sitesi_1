from functools import wraps
import hashlib
import json
import os
import redis.asyncio as redis

# Mock Redis for MVP without spinning up container
class MockRedis:
    _store = {}
    async def get(self, key): return self._store.get(key)
    async def set(self, key, val, ex=None): self._store[key] = val

REDIS_URL = os.environ.get("REDIS_URL")
r = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True) if REDIS_URL else MockRedis()

def cache_search(ttl_seconds=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Generate Key
            # Naive key generation: Function name + kwargs
            key_parts = [func.__name__]
            for k, v in sorted(kwargs.items()):
                # Skip db session and objects
                if k not in ['db', 'background_tasks']:
                    key_parts.append(f"{k}:{v}")
            
            key_str = "|".join(key_parts)
            cache_key = f"cache:search:{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # 2. Check Cache
            cached = await r.get(cache_key)
            if cached:
                print(f"⚡ Cache Hit: {cache_key}")
                return json.loads(cached)
            
            # 3. Call Function
            result = await func(*args, **kwargs)
            
            # 4. Save Cache
            # Serialize Pydantic/Dict
            if hasattr(result, 'model_dump'):
                data = result.model_dump()
            elif isinstance(result, dict):
                data = result
            else:
                data = result # Hope it's serializable
                
            await r.set(cache_key, json.dumps(data, default=str), ex=ttl_seconds)
            print(f"💾 Cache Miss (Stored): {cache_key}")
            
            return result
        return wrapper
    return decorator
