
import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import structlog

logger = structlog.get_logger("access")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            raise e
        finally:
            process_time = time.time() - start_time
            
            # Extract User ID if available (from Auth Middleware)
            # Assuming auth middleware runs before or attached to request state
            user_id = getattr(request.state, "user_id", None)
            
            logger.info(
                "http_request",
                method=request.method,
                path=request.url.path,
                status=status_code,
                latency_ms=round(process_time * 1000, 2),
                user_id=str(user_id) if user_id else None,
                ip=request.client.host if request.client else None
            )
            
        return response
