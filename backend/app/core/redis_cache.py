
import os
import json
import hashlib
import gzip
import logging
from typing import Optional, Any
from functools import wraps
import redis.asyncio as redis # Using redis-py async

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.client: Optional[redis.Redis] = None
        self.enabled = os.environ.get("ENABLE_REDIS_CACHE", "true").lower() == "true"

    async def connect(self):
        if not self.enabled: return
        try:
            self.client = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self.client.ping()
            logger.info("✅ Redis Cache Connected")
        except Exception as e:
            logger.error(f"❌ Redis Connection Failed: {e}")
            self.client = None

    async def close(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str) -> Optional[Any]:
        if not self.client: return None
        try:
            # We store GZIP compressed bytes? Or just strings.
            # Spec says GZIP if large. For simplicity, let's store JSON strings first.
            # If we use decode_responses=True, we get strings.
            val = await self.client.get(key)
            if val:
                return json.loads(val)
        except Exception as e:
            logger.warning(f"Cache GET error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = 60):
        if not self.client: return
        try:
            val_str = json.dumps(value)
            await self.client.set(key, val_str, ex=ttl)
        except Exception as e:
            logger.warning(f"Cache SET error: {e}")

    async def clear_by_pattern(self, pattern: str):
        """Clear keys matching pattern (e.g. 'search:v2:*')"""
        if not self.client: return
        try:
            # SCAN is safer than KEYS for production
            cursor = 0
            while True:
                cursor, keys = await self.client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self.client.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"🧹 Cache cleared for pattern: {pattern}")
        except Exception as e:
            logger.error(f"❌ Cache CLEAR error: {e}")

# Singleton
cache_service = RedisCache()

# Decorator Helper
def build_cache_key(prefix: str, **kwargs) -> str:
    """Canonicalize kwargs to create stable key"""
    # 1. Filter out None
    clean_kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    # 2. Sort Keys
    sorted_items = sorted(clean_kwargs.items())
    
    # 3. Hash
    payload = json.dumps(sorted_items, sort_keys=True)
    hash_val = hashlib.sha256(payload.encode()).hexdigest()
    
    return f"{prefix}:{hash_val}"
