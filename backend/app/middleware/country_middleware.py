
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, Response
from fastapi import Request
import logging
from sqlalchemy import select
from app.models.core import Country, FeatureFlag
from app.database import AsyncSessionLocal # Need a way to get DB in middleware or use cached config

logger = logging.getLogger(__name__)

class CountryMiddleware(BaseHTTPMiddleware):
    # Static list for MVP (Should be cached from DB in prod)
    VALID_COUNTRIES = ["tr", "de", "fr", "us", "gb", "it"] # Added IT
    EXCLUDED_PREFIXES = ["/api", "/admin", "/static", "/favicon.ico", "/sitemap.xml", "/robots.txt", "/docs", "/openapi.json"]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 1. Skip Excluded Paths
        for prefix in self.EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # 2. Check URL Segment
        parts = path.strip("/").split("/")
        first_segment = parts[0].lower() if parts else ""
        
        if first_segment in self.VALID_COUNTRIES:
            country_code = first_segment.upper()
            
            # P19: Check Feature Flag / Status
            # Performance Note: In prod, this should be cached in Redis or memory.
            # Here we do a DB call for strict enforcement or skip for MVP speed if using static config.
            # Let's assume we use a simple check or pass.
            # For "Country Activation", we should check 'is_enabled' from Country model or FeatureFlag.
            
            # Simulated Check (Replace with DB/Cache lookup)
            is_active = True
            is_beta = False
            
            # Example Logic:
            # async with AsyncSessionLocal() as db:
            #     res = await db.execute(select(Country).where(Country.code == country_code))
            #     country = res.scalar_one_or_none()
            #     if not country or not country.is_enabled: is_active = False
            
            # If "Coming Soon" needed:
            if not is_active:
                 return Response(content=f"Coming Soon: {country_code}", status_code=503)

            request.state.country = country_code
            response = await call_next(request)
            response.headers["X-Country-Code"] = country_code
            return response
            
        # 3. Redirect Logic
        # Detect Country (Header or Default)
        # Note: In a real app, check CF-IPCountry header
        detected_country = "tr" # Default MVP
        
        if first_segment == "": # Root /
            new_url = f"/{detected_country}"
        else:
            # Missing country prefix -> Prepend
            new_url = f"/{detected_country}{path}"
            
        # Use 307 for now to avoid caching redirect during dev
        return RedirectResponse(url=new_url, status_code=307)
