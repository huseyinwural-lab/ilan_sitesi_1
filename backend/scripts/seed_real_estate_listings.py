
import asyncio
import logging
import sys
import os
import random
import uuid
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.dealer import Dealer
from app.models.moderation import Listing
from app.models.category import Category
from app.models.attribute import Attribute

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("re_seed")

# CONFIG
COUNT_HOUSING = 60
COUNT_COMMERCIAL = 30

async def seed_real_estate():
    is_prod = os.environ.get("APP_ENV") == "production"
    
    # We allow this seed in prod ONLY if explicitly flagged, as it creates "Demo" content.
    # But generally blocked.
    if is_prod:
        logger.error("🚫 STOP: Production Requires Manual Override.")
        return

    logger.info("🏡 Starting Real Estate Listings Seed (v1)...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Context
            users = (await session.execute(select(User))).scalars().all()
            dealers = (await session.execute(select(Dealer))).scalars().all()
            cats = (await session.execute(select(Category).where(Category.module == 'real_estate'))).scalars().all()
            
            # Organize Cats
            housing_cats = [c for c in cats if 'housing' in (c.path or '') or c.slug.get('en') in ['apartment-sale', 'house-sale', 'apartment-rent', 'house-rent']]
            comm_cats = [c for c in cats if 'commercial' in (c.path or '') or c.slug.get('en') in ['office', 'retail', 'warehouse']]
            
            if not housing_cats or not comm_cats:
                logger.error("❌ Categories not found! Run seed_production_data_v2.py first.")
                return

            # 2. Cleanup Old Seed
            logger.info("Cleaning previous Real Estate seed data...")
            await session.execute(delete(Listing).where(Listing.description.like("%Generated Real Estate Listing%")))
            await session.commit()

            # 3. Generators
            def get_random_owner():
                if random.random() < 0.8 and dealers:
                    d = random.choice(dealers)
                    return d.id, True, users[0].id # Mock user link
                return None, False, random.choice(users).id

            def generate_attributes(cat_type, sale_type):
                # Global
                m2_gross = random.randint(50, 300) if cat_type == 'housing' else random.randint(100, 2000)
                m2_net = int(m2_gross * 0.85)
                
                attrs = {
                    "m2_gross": m2_gross,
                    "m2_net": m2_net,
                    "building_status": random.choice(["new", "used", "construction"]),
                    "heating_type": random.choice(["combi_gas", "central", "floor", "electric"]),
                    "eligible_for_bank": random.choice([True, False]),
                    "swap_available": random.choice([True, False]),
                    "dues": random.randint(0, 200)
                }

                if cat_type == 'housing':
                    attrs.update({
                        "room_count": random.choices(["1+1", "2+1", "3+1", "4+1"], weights=[20, 40, 30, 10])[0],
                        "floor_location": random.choice(["1", "2", "3", "4", "5-10", "top"]),
                        "bathroom_count": "1" if m2_gross < 120 else "2",
                        "balcony": random.choice([True, False]),
                        "furnished": True if sale_type == 'rent' and random.random() < 0.3 else False,
                        "in_complex": random.choice([True, False])
                    })
                elif cat_type == 'commercial':
                    attrs.update({
                        "ceiling_height": round(random.uniform(2.8, 6.0), 1),
                        "entrance_height": round(random.uniform(2.2, 4.5), 1),
                        "power_capacity": random.randint(10, 150),
                        "crane": random.choice([True, False]),
                        "is_transfer": True if sale_type == 'rent' and random.random() < 0.2 else False,
                        "ground_survey": random.choice(["done", "not_done"])
                    })
                
                return attrs

            def generate_media():
                count = random.randint(5, 10)
                base = "https://picsum.photos/seed"
                return [f"{base}/{uuid.uuid4()}/800/600" for _ in range(count)]

            # 4. Generate Housing
            for i in range(COUNT_HOUSING):
                cat = random.choice(housing_cats)
                is_rent = 'rent' in (cat.slug.get('en') or '')
                dealer_id, is_dealer, user_id = get_random_owner()
                country = random.choice(["DE", "TR", "FR"])
                
                status_pool = ["active"] * 6 + ["pending"] * 2 + ["rejected"] * 2
                status = random.choice(status_pool)

                listing = Listing(
                    title=f"{'Rent' if is_rent else 'Sale'} {cat.slug.get('en')} - {random.randint(1,99)}",
                    description="Generated Real Estate Listing v1. High quality property.",
                    module="real_estate",
                    category_id=cat.id,
                    country=country,
                    city="Berlin" if country == "DE" else ("Istanbul" if country == "TR" else "Paris"),
                    price=random.randint(500, 3000) if is_rent else random.randint(100000, 900000),
                    currency="EUR", # Keep simple
                    user_id=user_id,
                    dealer_id=dealer_id,
                    is_dealer_listing=is_dealer,
                    status=status,
                    images=generate_media(),
                    image_count=5,
                    attributes=generate_attributes('housing', 'rent' if is_rent else 'sale'),
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 60))
                )
                session.add(listing)

            # 5. Generate Commercial
            for i in range(COUNT_COMMERCIAL):
                cat = random.choice(comm_cats)
                dealer_id, is_dealer, user_id = get_random_owner()
                country = random.choice(["DE", "TR", "FR"])
                
                listing = Listing(
                    title=f"Commercial {cat.slug.get('en')} - {random.randint(1,99)}",
                    description="Generated Real Estate Listing v1. Prime location.",
                    module="real_estate",
                    category_id=cat.id,
                    country=country,
                    city="Munich" if country == "DE" else ("Ankara" if country == "TR" else "Lyon"),
                    price=random.randint(200000, 2000000),
                    currency="EUR",
                    user_id=user_id,
                    dealer_id=dealer_id,
                    is_dealer_listing=is_dealer,
                    status="active",
                    images=generate_media(),
                    image_count=5,
                    attributes=generate_attributes('commercial', 'sale'),
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)

            await session.commit()
            logger.info(f"✅ Created {COUNT_HOUSING + COUNT_COMMERCIAL} Real Estate Listings.")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_real_estate())
