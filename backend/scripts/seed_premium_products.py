
import asyncio
import os
import sys
import uuid
from decimal import Decimal
from sqlalchemy import select, and_

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.premium import PremiumProduct

async def seed_premium_products():
    print("🚀 Seeding Premium Products...")
    
    # Define Products (TRY based on P17 Matrix)
    # Adapting for generic EUR/USD later via currency map, but hardcoding TRY for now as per matrix
    
    products = [
        # SHOWCASE
        {
            "key": "SHOWCASE_7D",
            "name": {"tr": "Vitrin (1 Hafta)", "en": "Showcase (1 Week)"},
            "description": {"tr": "İlanınız 1 hafta boyunca vitrinde kalsın."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 250.00,
            "duration_days": 7,
            "tax_category": "advertising"
        },
        {
            "key": "SHOWCASE_30D",
            "name": {"tr": "Vitrin (4 Hafta)", "en": "Showcase (4 Weeks)"},
            "description": {"tr": "İlanınız 30 gün boyunca vitrinde kalsın."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 750.00, # 3x price for 4x duration (discounted)
            "duration_days": 30,
            "tax_category": "advertising"
        },
        # BOOST (Doping)
        {
            "key": "BOOST_1",
            "name": {"tr": "Yukarı Taşı", "en": "Boost"},
            "description": {"tr": "İlanınızı listenin en üstüne taşıyın."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 50.00,
            "duration_days": 0, # Immediate effect
            "tax_category": "digital_service"
        },
        {
            "key": "BOOST_5",
            "name": {"tr": "5'li Doping Paketi", "en": "5x Boost Pack"},
            "description": {"tr": "5 adet yukarı taşıma hakkı."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 200.00, # Bulk discount
            "duration_days": 0, # Credit based?
            # Note: Implementing packs requires a "Credit" system for Boosts.
            # For P17 MVP, let's treat this as buying 5 credits if system supports it, 
            # OR just buying 1 product that triggers 5 increments?
            # Current User model doesn't have "boost_credits". 
            # P17 Dealer Plan Matrix mentioned "Boost Hakkı".
            # So DealerSubscription probably tracks quotas.
            # But individual users?
            # Let's stick to Single Boost for now to simplify "Pay & Apply".
            # Packs can be added later if we add a "Wallet" or "Quota" model for individuals.
            # SKIPPING BOOST_5 for now to avoid scope creep on Wallet.
            # "duration_days": 0
        },
        # URGENT
        {
            "key": "URGENT_7D",
            "name": {"tr": "Acil Acil", "en": "Urgent"},
            "description": {"tr": "Acil etiketi ile dikkat çekin."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 100.00,
            "duration_days": 7,
            "tax_category": "advertising"
        },
        # BOLD TITLE
        {
            "key": "BOLD_TITLE",
            "name": {"tr": "Kalın Başlık", "en": "Bold Title"},
            "description": {"tr": "İlan başlığınız koyu renkle ayrışsın."},
            "country": "TR",
            "currency": "TRY",
            "price_net": 75.00,
            "duration_days": 30, # Assuming listing duration or fixed
            "tax_category": "digital_service"
        }
    ]

    async with AsyncSessionLocal() as session:
        for p_data in products:
            # Check exist
            stmt = select(PremiumProduct).where(and_(
                PremiumProduct.key == p_data["key"],
                PremiumProduct.country == p_data["country"]
            ))
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()
            
            if not existing:
                if p_data["key"] == "BOOST_5": continue # Skip as discussed
                
                prod = PremiumProduct(
                    key=p_data["key"],
                    name=p_data["name"],
                    description=p_data["description"],
                    country=p_data["country"],
                    currency=p_data["currency"],
                    price_net=Decimal(str(p_data["price_net"])),
                    duration_days=p_data["duration_days"],
                    tax_category=p_data["tax_category"],
                    is_active=True
                )
                session.add(prod)
                print(f"➕ Added: {p_data['key']}")
            else:
                print(f"ℹ️ Exists: {p_data['key']}")
        
        await session.commit()
    print("✅ Seeding Complete.")

if __name__ == "__main__":
    asyncio.run(seed_premium_products())
