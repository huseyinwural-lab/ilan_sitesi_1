
import redis.asyncio as redis
import time
import logging
from typing import Optional

logger = logging.getLogger("rate_limit")

# Lua Script for Token Bucket
# Keys: {key}
# Args: capacity, refill_rate, now_timestamp, requested_tokens
LUA_TOKEN_BUCKET = """
local key = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- Get current state
local tokens = tonumber(redis.call('HGET', key, 'tokens'))
local last_refill = tonumber(redis.call('HGET', key, 'last_refill'))

if tokens == nil then
    tokens = capacity
    last_refill = now
end

-- Refill
local delta = math.max(0, now - last_refill)
local filled_tokens = math.min(capacity, tokens + (delta * refill_rate))

-- Consume
local allowed = 0
if filled_tokens >= requested then
    allowed = 1
    filled_tokens = filled_tokens - requested
end

-- Update
redis.call('HSET', key, 'tokens', filled_tokens, 'last_refill', now)
redis.call('EXPIRE', key, 60) -- Auto cleanup after 1 min idle

return {allowed, filled_tokens}
"""

class RedisRateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        self._script = self.redis.register_script(LUA_TOKEN_BUCKET)

    async def check_limit(self, key: str, limit: int, burst: int = 0) -> bool:
        """
        Checks if request is allowed using Token Bucket.
        limit: Requests per minute (Rate).
        burst: Max concurrent requests (Capacity).
        """
        capacity = burst if burst > 0 else limit
        refill_rate = limit / 60.0 # Tokens per second
        now = time.time()
        
        try:
            # Atomic Lua Execution
            result = await self._script(
                keys=[key],
                args=[capacity, refill_rate, now, 1]
            )
            
            allowed = bool(result[0])
            remaining = float(result[1])
            
            return allowed
            
        except Exception as e:
            logger.error(f"Redis Error: {e}")
            # Fail Open
            return True

    async def close(self):
        await self.redis.close()
