
import asyncio
import logging
import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.dealer import Dealer
from app.models.moderation import Listing
from app.models.category import Category

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_vehicle_listings")

COUNT_CARS = 70
COUNT_MOTO = 30
COUNT_COMM = 20

async def seed_vehicle_listings():
    is_prod = os.environ.get("APP_ENV") == "production"
    
    if is_prod and "--allow-prod" not in sys.argv:
        logger.error("🚫 STOP: Production Requires --allow-prod flag.")
        return

    logger.info("🚗 Starting Vehicle Listings Seed v4...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Context
            users = (await session.execute(select(User))).scalars().all()
            dealers = (await session.execute(select(Dealer))).scalars().all()
            cats = (await session.execute(select(Category).where(Category.module == 'vehicle'))).scalars().all()
            
            # Organize Cats
            car_cats = []
            moto_cats = []
            comm_cats = []
            
            for c in cats:
                slug = c.slug.get('en') if isinstance(c.slug, dict) else c.slug
                if not slug: continue
                
                if slug in ['cars', 'used-cars', 'new-cars']:
                    car_cats.append(c)
                elif slug in ['motorcycles', 'scooter', 'racing']: # Assuming subcats might exist or just root moto
                    moto_cats.append(c)
                elif slug in ['commercial-vehicles', 'van', 'truck']:
                    comm_cats.append(c)
            
            # Fallback if specific subs not found, use roots
            if not car_cats: car_cats = [c for c in cats if 'cars' in str(c.slug)]
            if not moto_cats: moto_cats = [c for c in cats if 'motorcycles' in str(c.slug)]
            if not comm_cats: comm_cats = [c for c in cats if 'commercial' in str(c.slug)]

            if not car_cats or not moto_cats:
                logger.error("❌ Categories not found! Run seed_production_data_v4.py first.")
                return

            # 2. Cleanup Old Vehicles
            logger.info("Cleaning ALL Vehicle listings...")
            await session.execute(delete(Listing).where(Listing.module == 'vehicle'))
            await session.commit()

            # 3. Generators
            def get_random_owner():
                if random.random() < 0.8 and dealers:
                    d = random.choice(dealers)
                    return d.id, True, users[0].id
                return None, False, random.choice(users).id

            def generate_media():
                count = random.randint(5, 10)
                base = "https://picsum.photos/seed"
                return [f"{base}/{uuid.uuid4()}/800/600" for _ in range(count)]

            brands = {
                "cars": ["bmw", "mercedes", "audi", "vw", "tesla", "toyota", "ford", "renault"],
                "moto": ["yamaha", "honda", "ducati", "kawasaki"],
                "comm": ["ford", "mercedes", "renault", "iveco"]
            }

            def generate_attributes(v_type):
                # Global
                brand = random.choice(brands.get(v_type, brands["cars"]))
                attrs = {
                    "brand": brand,
                    "model": f"Model {random.randint(1,999)}",
                    "year": random.randint(2010, 2025),
                    "km": random.randint(0, 250000),
                    "condition": random.choice(["used", "new", "damaged"]),
                    "warranty": random.choice([True, False]),
                    "swap": random.choice([True, False]),
                    "fuel_type": random.choice(["gasoline", "diesel", "hybrid", "electric"])
                }

                if v_type == "cars":
                    attrs.update({
                        "gear_type": random.choice(["manual", "automatic", "semi"]),
                        "body_type": random.choice(["sedan", "suv", "hatchback", "station"]),
                        "engine_power_kw": random.randint(60, 300),
                        "engine_capacity_cc": random.randint(1000, 3000),
                        "drive_train": random.choice(["fwd", "rwd", "4wd"]),
                        "emission_class": random.choice(["euro6", "euro5", "euro4"]),
                        "inspection_valid": random.choice([True, False]),
                        "navigation": random.choice([True, False]),
                        "leather_seats": random.choice([True, False]),
                        "air_condition": random.choice(["auto", "manual", "none"])
                    })
                elif v_type == "moto":
                    attrs.update({
                        "moto_type": random.choice(["scooter", "racing", "chopper", "naked"]),
                        "abs": random.choice([True, False]),
                        "engine_capacity_cc": random.randint(50, 1200),
                        "engine_power_kw": random.randint(5, 150)
                    })
                elif v_type == "comm":
                    attrs.update({
                        "comm_vehicle_type": random.choice(["van", "truck", "bus"]),
                        "load_capacity_kg": random.randint(1000, 20000),
                        "box_type": random.choice(["closed", "open", "frigo"])
                    })
                
                return attrs

            # 4. Create Cars
            for i in range(COUNT_CARS):
                cat = random.choice(car_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                attrs = generate_attributes("cars")
                title = f"{attrs['brand'].upper()} {attrs['model']} {attrs['year']} - {country}"
                
                listing = Listing(
                    title=title,
                    description="Premium vehicle in great condition.",
                    module="vehicle",
                    category_id=cat.id,
                    country=country,
                    city="Berlin" if country == "DE" else ("Istanbul" if country == "TR" else "Paris"),
                    price=random.randint(10000, 150000),
                    currency="EUR",
                    user_id=user_id,
                    dealer_id=dealer_id,
                    is_dealer_listing=is_dealer,
                    status="active",
                    images=generate_media(),
                    image_count=8,
                    attributes=attrs,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)

            # 5. Create Moto
            for i in range(COUNT_MOTO):
                cat = random.choice(moto_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                attrs = generate_attributes("moto")
                title = f"{attrs['brand'].upper()} Moto {attrs['year']}"
                
                listing = Listing(
                    title=title,
                    description="Fast and reliable.",
                    module="vehicle",
                    category_id=cat.id,
                    country=country,
                    city="Munich",
                    price=random.randint(2000, 20000),
                    currency="EUR",
                    user_id=user_id,
                    dealer_id=dealer_id,
                    is_dealer_listing=is_dealer,
                    status="active",
                    images=generate_media(),
                    image_count=5,
                    attributes=attrs,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)

            # 6. Create Commercial
            for i in range(COUNT_COMM): # Fixed var name
                if not comm_cats: break
                cat = random.choice(comm_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                attrs = generate_attributes("comm")
                title = f"{attrs['brand'].upper()} Transporter"
                
                listing = Listing(
                    title=title,
                    description="Heavy duty worker.",
                    module="vehicle",
                    category_id=cat.id,
                    country=country,
                    city="Hamburg",
                    price=random.randint(15000, 80000),
                    currency="EUR",
                    user_id=user_id,
                    dealer_id=dealer_id,
                    is_dealer_listing=is_dealer,
                    status="active",
                    images=generate_media(),
                    image_count=6,
                    attributes=attrs,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)

            await session.commit()
            logger.info(f"✅ Created {COUNT_CARS + COUNT_MOTO + COUNT_COMM} Vehicle Listings.")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_vehicle_listings())
