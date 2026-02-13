
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from asgi_correlation_id import correlation_id
import structlog
import traceback

logger = structlog.get_logger("error_handler")

def get_error_code(status_code: int) -> str:
    codes = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        422: "validation_error",
        429: "rate_limit_exceeded",
        500: "internal_server_error"
    }
    return codes.get(status_code, "unknown_error")

async def global_exception_handler(request: Request, exc: Exception):
    req_id = correlation_id.get() or "unknown"
    
    # 1. Validation Errors (Pydantic)
    if isinstance(exc, RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Input validation failed",
                    "request_id": req_id,
                    "details": exc.errors()
                }
            }
        )

    # 2. HTTP Exceptions (FastAPI/Starlette)
    if isinstance(exc, (HTTPException, StarletteHTTPException)):
        code = getattr(exc, "detail", {}).get("code") if isinstance(exc.detail, dict) else get_error_code(exc.status_code)
        message = getattr(exc, "detail", {}).get("message") if isinstance(exc.detail, dict) else str(exc.detail)
        
        # If detail is string, use it as message
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "request_id": req_id
                }
            },
            headers=getattr(exc, "headers", None)
        )

    # 3. Uncaught Server Errors
    logger.error("internal_server_error", error=str(exc), traceback=traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An internal error occurred.",
                "request_id": req_id
            }
        }
    )
