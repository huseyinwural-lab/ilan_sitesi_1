
from fastapi import APIRouter, Depends, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.category import Category
import os
import urllib.parse
import re

router = APIRouter(tags=["seo"])


def _resolve_domain(request: Request) -> str | None:
    env_url = (os.environ.get("PUBLIC_BASE_URL") or "").strip()
    if env_url:
        parsed = urllib.parse.urlparse(env_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme or "https").split(",")[0].strip()
    host = (request.headers.get("x-forwarded-host") or request.headers.get("host") or "").split(",")[0].strip()
    if host:
        parsed = urllib.parse.urlparse(f"{proto}://{host}")
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
    return None


def _norm_path(path: str) -> str:
    normalized = "/" + (path or "").lstrip("/")
    normalized = re.sub(r"/+", "/", normalized)
    if normalized != "/" and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized

@router.get("/robots.txt", response_class=Response)
async def get_robots_txt(request: Request):
    domain = _resolve_domain(request)
    if not domain:
        return Response(content="PUBLIC_BASE_URL missing", media_type="text/plain")
    content = f"""User-agent: *
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/
Allow: /

Sitemap: {domain}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

@router.get("/sitemap.xml", response_class=Response)
async def get_sitemap_index(request: Request):
    domain = _resolve_domain(request)
    if not domain:
        return Response(content="<error>PUBLIC_BASE_URL missing</error>", media_type="application/xml")
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <sitemap>
      <loc>{domain}/sitemaps/static.xml</loc>
   </sitemap>
   <sitemap>
      <loc>{domain}/sitemaps/listings.xml</loc>
   </sitemap>
   <sitemap>
      <loc>{domain}/sitemaps/categories.xml</loc>
   </sitemap>
</sitemapindex>
"""
    return Response(content=content, media_type="application/xml")

@router.get("/sitemaps/listings.xml", response_class=Response)
async def get_listings_sitemap(request: Request, db: AsyncSession = Depends(get_db)):
    domain = _resolve_domain(request)
    if not domain:
        return Response(content="<error>PUBLIC_BASE_URL missing</error>", media_type="application/xml")
    # CRITICAL SEO CHECK: Only Active Listings
    query = select(Listing.id, Listing.updated_at).where(Listing.status == 'active').limit(50000)
    result = await db.execute(query)
    listings = result.all()
    
    xml_items = []
    for listing_row in listings:
        # Assuming slug generation logic is consistent with frontend
        url = f"{domain}{_norm_path(f'/listing/{listing_row.id}')}" 
        lastmod = listing_row.updated_at.strftime("%Y-%m-%d") if listing_row.updated_at else ""
        xml_items.append(f"""
   <url>
      <loc>{url}</loc>
      <lastmod>{lastmod}</lastmod>
      <changefreq>daily</changefreq>
      <priority>0.8</priority>
   </url>""")
    
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(xml_items)}
</urlset>
"""
    return Response(content=content, media_type="application/xml")

@router.get("/sitemaps/categories.xml", response_class=Response)
async def get_categories_sitemap(request: Request, db: AsyncSession = Depends(get_db)):
    domain = _resolve_domain(request)
    if not domain:
        return Response(content="<error>PUBLIC_BASE_URL missing</error>", media_type="application/xml")
    query = select(Category).where(Category.is_enabled.is_(True))
    result = await db.execute(query)
    cats = result.scalars().all()
    
    xml_items = []
    for category_row in cats:
        slug = category_row.slug.get('en', 'category')
        url = f"{domain}{_norm_path(f'/category/{slug}') }"
        xml_items.append(f"""
   <url>
      <loc>{url}</loc>
      <changefreq>weekly</changefreq>
      <priority>0.6</priority>
   </url>""")
        
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{''.join(xml_items)}
</urlset>
"""
    return Response(content=content, media_type="application/xml")
