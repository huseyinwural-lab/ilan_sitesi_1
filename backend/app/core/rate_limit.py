
import time
from fastapi import Request, HTTPException, Depends
from starlette.responses import JSONResponse
import logging
import os
from typing import Optional, Tuple, Callable

logger = logging.getLogger("rate_limiter")

# In-memory storage: {key: [timestamp1, timestamp2, ...]}
_rate_limit_store = {}

def clean_expired_entries(window_seconds: int):
    """Cleanup helper (Naive implementation)"""
    now = time.time()
    keys_to_delete = []
    for key, timestamps in _rate_limit_store.items():
        valid_timestamps = [t for t in timestamps if t > now - window_seconds]
        if not valid_timestamps:
            keys_to_delete.append(key)
        else:
            _rate_limit_store[key] = valid_timestamps
    for k in keys_to_delete:
        del _rate_limit_store[k]

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, scope: str = "default"):
        self.limit = limit
        self.window_seconds = window_seconds
        self.scope = scope
        self.enabled = os.environ.get("RATE_LIMIT_ENABLED", "True").lower() == "true"

    async def __call__(self, request: Request, user_id: Optional[str] = None):
        if not self.enabled:
            logger.debug(f"Rate limiting disabled for {self.scope}")
            return

        # Determine Key (Tier 1 vs Tier 2)
        # We assume user_id might be passed via Depends elsewhere, but here we are a Dependency.
        # Actually, to get user_id in Dependency, we need to inspect request state or use another dependency.
        # FastAPI resolves dependencies recursively.
        # If we want this to be a simple decorator usage like `Depends(RateLimiter(...))`, 
        # accessing user_id is tricky if it's not yet resolved.
        # 
        # Strategy: Check Request.state.user (if auth middleware set it) or fallback to IP.
        # Our Auth dependency returns User object.
        # We'll use IP as fallback.
        
        # Get IP from various headers (for proxy/load balancer scenarios)
        ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            request.headers.get("X-Real-IP") or
            (request.client.host if request.client else "127.0.0.1")
        )
        key_prefix = f"rl:{self.scope}"
        
        logger.info(f"Rate limiter {self.scope}: IP={ip}, enabled={self.enabled}")
        
        # Try to find user in state (if attached by middleware)
        # OR we can parse Bearer header manually for a "Tier 1" guess without full verification (risky?)
        # Better: We rely on the endpoint needing User dependency.
        # BUT RateLimiter runs *before* endpoint body.
        # Standard FastAPI Limiter often uses `request.user` if available.
        
        # For P5-007, let's use a simpler approach:
        # If Authorization header exists, use a hash of token as key (Tier 1 Proxy), or better,
        # just default to IP for unauth endpoints, and expect the caller to pass user_id if authenticated context is known.
        
        # Wait, `Depends` class style doesn't easily allow passing arguments from *other* dependencies computed at runtime 
        # unless we chain them.
        # 
        # Let's check `request.state`.
        
        user_identifier = ip
        tier = "ip"
        
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # We treat it as potentially authenticated user (Tier 1)
            # We use the token itself as the key to avoid full DB lookup overhead in the limiter 
            # (or simple hash of it).
            # This is "Token-Based" limiting.
            token = auth_header.split(" ")[1]
            user_identifier = token[-10:] # Last 10 chars as key proxy
            tier = "token"
        
        # Override for strict user_id if we can access it (maybe added by auth middleware later?)
        # For now token/ip distinction is robust enough for spec.
        
        key = f"{key_prefix}:{tier}:{user_identifier}"
        
        now = time.time()
        window_start = now - self.window_seconds
        
        # Fetch History
        history = _rate_limit_store.get(key, [])
        
        # Filter valid
        valid_history = [t for t in history if t > window_start]
        
        # Count
        current_usage = len(valid_history)
        
        logger.info(f"Rate limit check {key}: {current_usage}/{self.limit} requests in window")
        
        if current_usage >= self.limit:
            retry_after = int(self.window_seconds - (now - valid_history[0])) if valid_history else self.window_seconds
            logger.warning(f"Rate Limit Exceeded: {key} ({current_usage}/{self.limit})")
            
            raise HTTPException(
                status_code=429,
                detail={
                    "code": "rate_limit_exceeded",
                    "detail": "Too many requests. Please try again later.",
                    "meta": {
                        "limit_key": key,
                        "retry_after_seconds": retry_after
                    }
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(now + retry_after))
                }
            )
            
        # Record new request
        valid_history.append(now)
        _rate_limit_store[key] = valid_history
        
        logger.debug(f"Rate limit recorded for {key}: {len(valid_history)}/{self.limit}")
        
        # Cleanup occasionally (Naive: on write)
        if len(_rate_limit_store) > 10000:
             _rate_limit_store.clear() # Emergency dump
             
        # Ideally return something to set headers on response?
        # FastAPI dependencies can't easily modify response headers of the *success* case 
        # unless we use a Middleware or Response object.
        # We will skip success headers for MVP or add them if using Middleware.
        # But failure headers are Critical.
        
