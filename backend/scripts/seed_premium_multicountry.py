
import asyncio
import os
import sys
import uuid
from decimal import Decimal
from sqlalchemy import text, select, and_

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.premium import PremiumProduct

async def seed_premium_multicountry():
    print("🚀 Seeding Multi-Country Premium Products...")
    
    products = [
        # TR Products (TRY) - Already seeded partly in P17, reinforcing
        {
            "key": "SHOWCASE_7D_TR",
            "name": {"tr": "Vitrin (1 Hafta)", "en": "Showcase"},
            "price": 250.00,
            "currency": "TRY",
            "country": "TR",
            "duration": 7
        },
        # DE Products (EUR)
        {
            "key": "SHOWCASE_7D_DE",
            "name": {"de": "Schaufenster (1 Woche)", "en": "Showcase"},
            "price": 25.00,
            "currency": "EUR",
            "country": "DE",
            "duration": 7
        },
        {
            "key": "BOOST_1_DE",
            "name": {"de": "Push", "en": "Boost"},
            "price": 5.00,
            "currency": "EUR",
            "country": "DE",
            "duration": 0
        }
    ]

    async with AsyncSessionLocal() as session:
        for p in products:
            stmt = select(PremiumProduct).where(and_(
                PremiumProduct.key == p["key"],
                PremiumProduct.country == p["country"]
            ))
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                prod = PremiumProduct(
                    id=uuid.uuid4(),
                    key=p["key"],
                    name=p["name"],
                    description={},
                    price_net=Decimal(str(p["price"])),
                    currency=p["currency"],
                    duration_days=p["duration"],
                    tax_category="digital",
                    country=p["country"],
                    is_active=True,
                    sort_order=0
                )
                session.add(prod)
                print(f"➕ Added Product: {p['key']}")
            else:
                print(f"ℹ️ Product Exists: {p['key']}")
        
        await session.commit()
    print("✅ Premium Products Seeded.")

if __name__ == "__main__":
    asyncio.run(seed_premium_multicountry())
