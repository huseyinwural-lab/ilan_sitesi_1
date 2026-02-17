
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.category import Category
import os

router = APIRouter(tags=["seo"])

DOMAIN = os.environ.get("FRONTEND_URL", "https://platform.com")

@router.get("/robots.txt", response_class=Response)
async def get_robots_txt():
    content = f"""User-agent: *
Disallow: /admin/
Disallow: /dashboard/
Disallow: /api/
Allow: /

Sitemap: {DOMAIN}/sitemap.xml
"""
    return Response(content=content, media_type="text/plain")

@router.get("/sitemap.xml", response_class=Response)
async def get_sitemap_index():
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
   <sitemap>
      <loc>{DOMAIN}/sitemaps/static.xml</loc>
   </sitemap>
   <sitemap>
      <loc>{DOMAIN}/sitemaps/listings.xml</loc>
   </sitemap>
   <sitemap>
      <loc>{DOMAIN}/sitemaps/categories.xml</loc>
   </sitemap>
</sitemapindex>
"""
    return Response(content=content, media_type="application/xml")

@router.get("/sitemaps/listings.xml", response_class=Response)
async def get_listings_sitemap(db: AsyncSession = Depends(get_db)):
    # CRITICAL SEO CHECK: Only Active Listings
    query = select(Listing.id, Listing.updated_at).where(Listing.status == 'active').limit(50000)
    result = await db.execute(query)
    listings = result.all()
    
    xml_items = []
    for l in listings:
        # Assuming slug generation logic is consistent with frontend
        url = f"{DOMAIN}/listing/{l.id}" 
        lastmod = l.updated_at.strftime("%Y-%m-%d") if l.updated_at else ""
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
async def get_categories_sitemap(db: AsyncSession = Depends(get_db)):
    query = select(Category).where(Category.is_enabled == True)
    result = await db.execute(query)
    cats = result.scalars().all()
    
    xml_items = []
    for c in cats:
        slug = c.slug.get('en', 'category')
        url = f"{DOMAIN}/category/{slug}"
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
