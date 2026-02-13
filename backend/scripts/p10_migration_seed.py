
import asyncio
import os
import sys
from sqlalchemy import text
from datetime import datetime, timedelta, timezone

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import engine
from app.models.base import Base
from app.models.monetization import SubscriptionPlan

async def upgrade_db():
    print("🚀 Starting P10 Monetization Migration...")
    
    async with engine.begin() as conn:
        # 1. Create New Tables
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        # 2. Add Columns to Listings (Manual Alter)
        # We check if column exists first to be idempotent
        print("Checking listings table schema...")
        
        # is_showcase
        try:
            await conn.execute(text("ALTER TABLE listings ADD COLUMN is_showcase BOOLEAN DEFAULT FALSE"))
            print("✅ Added is_showcase")
        except Exception as e:
            if 'already exists' in str(e):
                print("ℹ️  is_showcase already exists")
            else:
                print(f"⚠️  Error: {e}")

        # showcase_expires_at
        try:
            await conn.execute(text("ALTER TABLE listings ADD COLUMN showcase_expires_at TIMESTAMPTZ DEFAULT NULL"))
            print("✅ Added showcase_expires_at")
        except Exception as e:
            if 'already exists' in str(e):
                print("ℹ️  showcase_expires_at already exists")
            else:
                print(f"⚠️  Error: {e}")

    # 3. Create Index (Concurrent not supported in transaction block, run separately)
    # We'll use raw connection for this
    
    print("Migration Complete (Tables & Columns).")

async def seed_plans():
    print("🌱 Seeding Default Subscription Plans...")
    from app.database import AsyncSessionLocal
    
    plans = [
        {
            "code": "TR_DEALER_BASIC",
            "name": {"en": "Basic Plan", "tr": "Temel Paket"},
            "price": 1000.00,
            "currency": "TRY",
            "duration": 30,
            "limits": {"listing": 10, "showcase": 0}
        },
        {
            "code": "TR_DEALER_PRO",
            "name": {"en": "Pro Plan", "tr": "Profesyonel Paket"},
            "price": 2500.00,
            "currency": "TRY",
            "duration": 30,
            "limits": {"listing": 50, "showcase": 5}
        },
        {
            "code": "TR_DEALER_ENTERPRISE",
            "name": {"en": "Enterprise Plan", "tr": "Kurumsal Paket"},
            "price": 10000.00,
            "currency": "TRY",
            "duration": 30,
            "limits": {"listing": 500, "showcase": 50}
        }
    ]

    async with AsyncSessionLocal() as session:
        # P10 Optimization: Ensure transaction is active for queries
        async with session.begin():
            for p in plans:
                # Check exist
                res = await session.execute(text(f"SELECT id FROM subscription_plans WHERE code = '{p['code']}'"))
            if not res.scalar_one_or_none():
                plan = SubscriptionPlan(
                    code=p['code'],
                    name=p['name'],
                    price=p['price'],
                    currency=p['currency'],
                    duration_days=p['duration'],
                    limits=p['limits']
                )
                session.add(plan)
                print(f"✅ Created Plan: {p['code']}")
            else:
                print(f"ℹ️  Plan {p['code']} exists")
        
        await session.commit()

if __name__ == "__main__":
    asyncio.run(upgrade_db())
    asyncio.run(seed_plans())
