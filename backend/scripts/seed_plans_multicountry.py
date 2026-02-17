
import asyncio
import os
import sys
import uuid
from decimal import Decimal
from sqlalchemy import text, select, and_

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.monetization import SubscriptionPlan

async def seed_plans_multicountry():
    print("🚀 Seeding Multi-Country Subscription Plans...")
    
    # Plans Definition
    plans = [
        # TR Plans (TRY)
        {
            "code": "DEALER_TR_BASIC",
            "name": {"tr": "Galeri Başlangıç", "en": "Dealer Basic"},
            "price": 500.00,
            "currency": "TRY",
            "country": "TR",
            "limits": {"listing": 10, "showcase": 0}
        },
        {
            "code": "DEALER_TR_PRO",
            "name": {"tr": "Galeri Pro", "en": "Dealer Pro"},
            "price": 1500.00,
            "currency": "TRY",
            "country": "TR",
            "limits": {"listing": 50, "showcase": 5}
        },
        # DE Plans (EUR)
        {
            "code": "DEALER_DE_BASIC",
            "name": {"de": "Händler Basis", "en": "Dealer Basic"},
            "price": 49.00,
            "currency": "EUR",
            "country": "DE",
            "limits": {"listing": 10, "showcase": 0}
        },
        {
            "code": "DEALER_DE_PRO",
            "name": {"de": "Händler Pro", "en": "Dealer Pro"},
            "price": 149.00,
            "currency": "EUR",
            "country": "DE",
            "limits": {"listing": 50, "showcase": 5}
        }
    ]

    async with AsyncSessionLocal() as session:
        for p in plans:
            # Check exist
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == p["code"])
            existing = (await session.execute(stmt)).scalar_one_or_none()
            
            if not existing:
                plan = SubscriptionPlan(
                    id=uuid.uuid4(),
                    code=p["code"],
                    name=p["name"],
                    description={},
                    price=Decimal(str(p["price"])),
                    currency=p["currency"],
                    duration_days=30,
                    limits=p["limits"],
                    is_active=True,
                    country_code=p["country"]
                )
                session.add(plan)
                print(f"➕ Added Plan: {p['code']}")
            else:
                print(f"ℹ️ Plan Exists: {p['code']}")
        
        await session.commit()
    print("✅ Plans Seeded.")

if __name__ == "__main__":
    asyncio.run(seed_plans_multicountry())
