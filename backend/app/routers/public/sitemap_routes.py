from fastapi import APIRouter, Response, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.core import Country
import os
import urllib.parse
import re

router = APIRouter()


def _resolve_base_url(request: Request) -> str | None:
    env_url = (os.environ.get("PUBLIC_BASE_URL") or "").strip()
    if env_url:
        parsed = urllib.parse.urlparse(env_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").split(",")[0].strip()
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
    if host:
        raw = f"{proto}://{host}"
        parsed = urllib.parse.urlparse(raw)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return None


def _clean_path(path: str) -> str:
    normalized = "/" + (path or "").lstrip("/")
    normalized = re.sub(r"/+", "/", normalized)
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized

@router.get("/sitemap.xml")
async def get_sitemap_index(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Sitemap Index
    """
    base_url = _resolve_base_url(request)
    if not base_url:
        return Response(content="<error>PUBLIC_BASE_URL missing</error>", media_type="application/xml")

    countries = (await db.execute(select(Country).where(Country.is_enabled.is_(True)))).scalars().all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for c in countries:
        xml += '  <sitemap>\n'
        xml += f'    <loc>{base_url}{_clean_path(f"/sitemap-{c.code.lower()}.xml")}</loc>\n'
        xml += '  </sitemap>\n'
        
    xml += '</sitemapindex>'
    return Response(content=xml, media_type="application/xml")

@router.get("/sitemap-{country_code}.xml")
async def get_country_sitemap(country_code: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Listing URLs for a specific country
    """
    country_code = country_code.upper()
    base_url = _resolve_base_url(request)
    if not base_url:
        return Response(content="<error>PUBLIC_BASE_URL missing</error>", media_type="application/xml")
    
    # Fetch active listings
    query = select(Listing.id, Listing.updated_at).where(
        Listing.country == country_code,
        Listing.status == 'active',
        Listing.deleted_at.is_(None),
        Listing.published_at.is_not(None),
    ).limit(10000) # Limit for MVP
    
    result = await db.execute(query)
    listings = result.all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for listing_row in listings:
        # Construct URL (Simplified, in reality needs slug lookup or storage)
        # Assuming we can generate slug or it's stored. 
        # For MVP, using ID-only pattern or fetching slug is too slow here without stored slug column.
        # Let's assume /ilan/{id} pattern for safety.
        url = f"{base_url}{_clean_path(f'/ilan/{listing_row.id}') }"
        lastmod = listing_row.updated_at.strftime("%Y-%m-%d")
        
        xml += '  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += '  </url>\n'
        
    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")
