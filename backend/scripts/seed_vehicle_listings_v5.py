
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
from app.models.vehicle_mdm import VehicleMake, VehicleModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_vehicle_listings_v5")

COUNT_CARS = 70
COUNT_MOTO = 30
COUNT_COMM = 20

async def seed_vehicle_listings_v5():
    is_prod = os.environ.get("APP_ENV") == "production"
    
    if is_prod and "--allow-prod" not in sys.argv:
        logger.error("🚫 STOP: Production Requires --allow-prod flag.")
        return

    logger.info("🚗 Starting Vehicle Listings Seed v5 (Master Data)...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Context
            users = (await session.execute(select(User))).scalars().all()
            dealers = (await session.execute(select(Dealer))).scalars().all()
            
            if not users:
                logger.error("❌ No Users found! Run seed_dummy_users.py first.")
                return

            # Use Fallback Logic for Categories
            cats = (await session.execute(select(Category).where(Category.module == 'vehicle'))).scalars().all()
            if not cats:
                logger.warning("No Vehicle Categories found in DB! Trying fallback fetch...")
                cats = (await session.execute(select(Category))).scalars().all()
                cats = [c for c in cats if c.module == 'vehicle']
            
            if not cats:
                logger.error("❌ Still no categories found. Run seed_production_data_v4.py")
                return

            # Organize Cats
            car_cats = [c for c in cats if 'cars' in str(c.slug)]
            moto_cats = [c for c in cats if 'motorcycles' in str(c.slug)]
            comm_cats = [c for c in cats if 'commercial' in str(c.slug)]
            
            # Fallback if specific subs not found, use roots
            if not car_cats: car_cats = cats
            if not moto_cats: moto_cats = cats
            if not comm_cats: comm_cats = cats

            makes = (await session.execute(select(VehicleMake))).scalars().all()
            models = (await session.execute(select(VehicleModel))).scalars().all()
            
            if not makes or not models:
                logger.error("❌ Master Data not found! Run seed_vehicle_master_data.py first.")
                return

            # Helper to get models for type
            def get_models(v_type):
                return [m for m in models if m.vehicle_type == v_type]

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

            def generate_attributes(v_type, model_obj):
                # Find Make
                make = next((m for m in makes if m.id == model_obj.make_id), None)
                make_name = make.name if make else "Unknown"
                
                attrs = {
                    "brand": make_name,
                    "model": model_obj.name,
                    "year": random.randint(2010, 2025),
                    "km": random.randint(0, 250000),
                    "condition": random.choice(["used", "new", "damaged"]),
                    "warranty": random.choice([True, False]),
                    "swap": random.choice([True, False]),
                    "fuel_type": random.choice(["gasoline", "diesel", "hybrid", "electric"])
                }

                if v_type == "car":
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
                
                return attrs, make.id, model_obj.id

            # 4. Create Cars
            car_models = get_models("car")
            if not car_models: logger.warning("No Car models found in Master Data!")
            
            for i in range(COUNT_CARS):
                cat = random.choice(car_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                model_obj = random.choice(car_models)
                attrs, make_id, model_id = generate_attributes("car", model_obj)
                
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
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                    make_id=make_id,   # Master Data Link
                    model_id=model_id  # Master Data Link
                )
                session.add(listing)

            # 5. Create Moto
            moto_models = get_models("moto")
            if not moto_models: logger.warning("No Moto models found!")

            for i in range(COUNT_MOTO):
                cat = random.choice(moto_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                model_obj = random.choice(moto_models)
                attrs, make_id, model_id = generate_attributes("moto", model_obj)
                
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
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                    make_id=make_id,
                    model_id=model_id
                )
                session.add(listing)

            # 6. Create Commercial
            comm_models = get_models("comm")
            if not comm_models: logger.warning("No Commercial models found!")

            for i in range(COUNT_COMM):
                cat = random.choice(comm_cats)
                country = random.choice(["DE", "TR", "FR"])
                dealer_id, is_dealer, user_id = get_random_owner()
                
                model_obj = random.choice(comm_models)
                attrs, make_id, model_id = generate_attributes("comm", model_obj)
                
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
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30)),
                    make_id=make_id,
                    model_id=model_id
                )
                session.add(listing)

            await session.commit()
            logger.info(f"✅ Created {COUNT_CARS + COUNT_MOTO + COUNT_COMM} Vehicle Listings (v5 Master Data).")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_vehicle_listings_v5())
