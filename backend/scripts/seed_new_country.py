
import asyncio
import os
import sys
import uuid
import argparse
from sqlalchemy import text, select, and_
from decimal import Decimal

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.core import Country
from app.models.category import Category
from app.models.monetization import SubscriptionPlan
from app.models.premium import PremiumProduct

async def seed_new_country(code: str, name_en: str, currency: str, lang: str):
    print(f"🚀 Launching New Country: {code} ({name_en})...")
    
    async with AsyncSessionLocal() as session:
        # 1. Create Country
        print("🔹 1. Creating Country...")
        stmt = select(Country).where(Country.code == code)
        existing = (await session.execute(stmt)).scalar_one_or_none()
        
        if not existing:
            country = Country(
                code=code,
                name={"en": name_en},
                default_currency=currency,
                default_language=lang,
                is_enabled=False # Start disabled (Soft Launch)
            )
            session.add(country)
            await session.commit()
            print("✅ Country Created")
        else:
            print("ℹ️ Country already exists")

        # 2. Copy Categories (Placeholder)
        # We don't need to copy if categories are global and translated.
        # But if we need country-specific category tree, we would clone here.
        # Current Architecture: Categories are global, 'allowed_countries' filters them.
        # So we just update allowed_countries for root categories?
        # Or assume all categories are open. P19.1 Decision: Global Tree.
        print("🔹 2. Config Categories... (Global Tree Assumption - No Action)")

        # 3. Create Default Subscription Plans
        print("🔹 3. Creating Plans...")
        plans = [
            {"tier": "BASIC", "price": 49.00 if currency == "EUR" else 500.00},
            {"tier": "PRO", "price": 149.00 if currency == "EUR" else 1500.00},
        ]
        
        for p in plans:
            plan_code = f"DEALER_{code}_{p['tier']}"
            stmt = select(SubscriptionPlan).where(SubscriptionPlan.code == plan_code)
            if not (await session.execute(stmt)).scalar_one_or_none():
                plan = SubscriptionPlan(
                    code=plan_code,
                    name={"en": f"Dealer {p['tier']}"},
                    country_code=code,
                    currency=currency,
                    price=Decimal(str(p["price"])),
                    duration_days=30,
                    limits={"listing": 10 if p["tier"] == "BASIC" else 50},
                    is_active=True
                )
                session.add(plan)
                print(f"➕ Added Plan: {plan_code}")
        
        # 4. Create Premium Products
        print("🔹 4. Creating Premium Products...")
        products = [
            {"key": f"SHOWCASE_7D_{code}", "price": 25.00 if currency == "EUR" else 250.00},
            {"key": f"BOOST_1_{code}", "price": 5.00 if currency == "EUR" else 50.00},
        ]
        
        for p in products:
            stmt = select(PremiumProduct).where(PremiumProduct.key == p["key"])
            if not (await session.execute(stmt)).scalar_one_or_none():
                prod = PremiumProduct(
                    key=p["key"],
                    country=code,
                    name={"en": "Premium Product"},
                    currency=currency,
                    price_net=Decimal(str(p["price"])),
                    duration_days=7 if "SHOWCASE" in p["key"] else 0,
                    is_active=True
                )
                session.add(prod)
                print(f"➕ Added Product: {p['key']}")

        await session.commit()
        print(f"✅ Launch Prep Complete for {code}!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--currency", required=True)
    parser.add_argument("--lang", required=True)
    args = parser.parse_args()
    
    asyncio.run(seed_new_country(args.code, args.name, args.currency, args.lang))
