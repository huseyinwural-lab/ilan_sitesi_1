import os
import redis.asyncio as redis

class CounterService:
    def __init__(self):
        self.redis = redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), encoding="utf-8", decode_responses=True)

    async def increment_unread(self, user_id: str):
        key = f"unread:user:{user_id}"
        await self.redis.incr(key)

    async def get_unread_count(self, user_id: str) -> int:
        key = f"unread:user:{user_id}"
        val = await self.redis.get(key)
        return int(val) if val else 0

    async def reset_unread(self, user_id: str):
        key = f"unread:user:{user_id}"
        await self.redis.set(key, 0)
        
    async def close(self):
        await self.redis.close()
