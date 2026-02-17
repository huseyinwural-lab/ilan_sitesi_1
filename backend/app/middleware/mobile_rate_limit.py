import os
from fastapi import Request, HTTPException
import logging
from app.core.redis_rate_limit import RedisRateLimiter

logger = logging.getLogger("rate_limit")

class MobileRateLimiter:
    def __init__(self):
        self.redis_limiter = RedisRateLimiter(redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

    async def __call__(self, request: Request):
        # 1. Identify Mobile Client
        user_agent = request.headers.get("user-agent", "").lower()
        device_id = request.headers.get("x-device-id", "unknown")
        
        # If not mobile, skip (or use standard limit)
        # if "emergent" not in user_agent and "flutter" not in user_agent:
        #     return # Pass through or apply standard web limits
            
        # 2. Key by Device ID (or IP as fallback)
        key = f"rl:mobile:{device_id if device_id != 'unknown' else request.client.host}"
        
        # 3. Check Limit (60 req/min for general API)
        allowed = await self.redis_limiter.check_limit(key, limit=60, burst=10)
        
        if not allowed:
            logger.warning(f"Mobile Rate Limit Exceeded: {key}")
            raise HTTPException(status_code=429, detail="Too Many Requests")

mobile_rate_limiter = MobileRateLimiter()
