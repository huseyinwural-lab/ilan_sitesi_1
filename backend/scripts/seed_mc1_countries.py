import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.core import Country

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def seed_mc1_countries():
    print("🌍 Seeding MC1 Countries (DE, AT, CH, FR)...")
    
    configs = [
        {"code": "DE", "name": {"en": "Germany", "de": "Deutschland"}, "lang": "de", "seo": "de-DE", "legal": {"imprint_required": True}},
        {"code": "AT", "name": {"en": "Austria", "de": "Österreich"}, "lang": "de", "seo": "de-AT", "legal": {"imprint_required": True}},
        {"code": "CH", "name": {"en": "Switzerland", "de": "Schweiz"}, "lang": "de", "seo": "de-CH", "legal": {"imprint_required": True}},
        {"code": "FR", "name": {"en": "France", "fr": "France"}, "lang": "fr", "seo": "fr-FR", "legal": {"imprint_required": False}},
        {"code": "TR", "name": {"en": "Turkey", "tr": "Türkiye"}, "lang": "tr", "seo": "tr-TR", "legal": {"imprint_required": False}}
    ]
    
    async with AsyncSessionLocal() as db:
        for c in configs:
            stmt = select(Country).where(Country.code == c["code"])
            country = (await db.execute(stmt)).scalar_one_or_none()
            
            if not country:
                country = Country(code=c["code"])
                db.add(country)
            
            country.name = c["name"]
            country.default_language = c["lang"]
            country.seo_locale = c["seo"]
            country.legal_info = c["legal"]
            country.default_currency = "EUR" # Forced Decision 2
            country.is_enabled = True
            
        await db.commit()
        print("✅ Countries Configured.")

if __name__ == "__main__":
    asyncio.run(seed_mc1_countries())
