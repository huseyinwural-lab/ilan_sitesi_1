from fastapi import APIRouter, Response, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db
from app.models.moderation import Listing
from app.models.core import Country

router = APIRouter()

BASE_URL = "https://platform.com"  # TODO: move to env/config

@router.get("/sitemap.xml")
async def get_sitemap_index(db: AsyncSession = Depends(get_db)):
    """
    Sitemap Index
    """
    countries = (await db.execute(select(Country).where(Country.is_enabled == True))).scalars().all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for c in countries:
        xml += '  <sitemap>\n'
        xml += f'    <loc>{BASE_URL}/sitemap-{c.code.lower()}.xml</loc>\n'
        xml += '  </sitemap>\n'
        
    xml += '</sitemapindex>'
    return Response(content=xml, media_type="application/xml")

@router.get("/sitemap-{country_code}.xml")
async def get_country_sitemap(country_code: str, db: AsyncSession = Depends(get_db)):
    """
    Listing URLs for a specific country
    """
    country_code = country_code.upper()
    
    # Fetch active listings
    query = select(Listing.id, Listing.updated_at).where(
        Listing.country == country_code,
        Listing.status == 'active'
    ).limit(10000) # Limit for MVP
    
    result = await db.execute(query)
    listings = result.all()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for l in listings:
        # Construct URL (Simplified, in reality needs slug lookup or storage)
        # Assuming we can generate slug or it's stored. 
        # For MVP, using ID-only pattern or fetching slug is too slow here without stored slug column.
        # Let's assume /ilan/{id} pattern for safety.
        url = f"{BASE_URL}/ilan/{l.id}"
        lastmod = l.updated_at.strftime("%Y-%m-%d")
        
        xml += '  <url>\n'
        xml += f'    <loc>{url}</loc>\n'
        xml += f'    <lastmod>{lastmod}</lastmod>\n'
        xml += '  </url>\n'
        
    xml += '</urlset>'
    return Response(content=xml, media_type="application/xml")
