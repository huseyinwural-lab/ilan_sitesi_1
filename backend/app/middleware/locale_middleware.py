from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from contextvars import ContextVar

# Context var to store current locale
locale_ctx = ContextVar("locale", default="en")

class LocaleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Check Header
        lang = request.headers.get("Accept-Language", "en").split(",")[0][:2]
        
        # 2. Check URL Prefix (Override)
        path_parts = request.url.path.strip("/").split("/")
        if path_parts and len(path_parts[0]) == 2:
            potential_lang = path_parts[0]
            if potential_lang in ["en", "de", "tr", "fr"]:
                lang = potential_lang
                
        # Set Context
        token = locale_ctx.set(lang)
        
        try:
            response = await call_next(request)
            return response
        finally:
            locale_ctx.reset(token)

def get_locale():
    return locale_ctx.get()
