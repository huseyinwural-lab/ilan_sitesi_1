
import asyncio
import logging
import sys
import os
import random
import uuid
import argparse
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.moderation import Listing
from app.models.category import Category
from app.models.attribute import Attribute, AttributeOption, ListingAttribute

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_shopping_listings")

COUNT_ELEC = 30
COUNT_FASH = 10
COUNT_HOME = 20

async def seed_shopping_listings_v6():
    is_prod = os.environ.get("APP_ENV") == "production"
    if is_prod and "--allow-prod" not in sys.argv:
        logger.error("🚫 STOP: Production Requires --allow-prod.")
        return

    logger.info("🛍️ Starting Shopping Listings Seed v6 (Attribute v2)...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Context
            users = (await session.execute(select(User))).scalars().all()
            if not users:
                logger.error("❌ No Users found! Run seed_dummy_users.py first.")
                return

            # Helper to find cat
            all_cats = (await session.execute(select(Category).where(Category.module == 'shopping'))).scalars().all()
            
            def get_cat(slug):
                return next((c for c in all_cats if c.slug.get('en') == slug), None)

            # Load Attributes & Options
            all_attrs = (await session.execute(select(Attribute))).scalars().all()
            all_opts = (await session.execute(select(AttributeOption))).scalars().all()
            
            attr_map = {a.key: a for a in all_attrs}
            opt_map = {} # key -> list of options
            for opt in all_opts:
                # Find parent key
                parent = next((a for a in all_attrs if a.id == opt.attribute_id), None)
                if parent:
                    if parent.key not in opt_map: opt_map[parent.key] = []
                    opt_map[parent.key].append(opt)

            # 2. Cleanup Old Shopping Listings
            logger.info("Cleaning ALL Shopping listings...")
            await session.execute(delete(Listing).where(Listing.module == 'shopping'))
            # We should also clean ListingAttribute table but CASCADE delete on FK handles it?
            # Yes, ondelete="CASCADE" is set.
            await session.commit()

            # 3. Helpers
            def get_user(): return random.choice(users).id
            
            def generate_media(cat_type):
                base = "https://picsum.photos/seed"
                return [f"{base}/{uuid.uuid4()}/800/600" for _ in range(4)]

            async def create_listing(title, cat, price, attributes_data):
                user_id = get_user()
                listing = Listing(
                    title=title,
                    description=f"Great condition {title}. Selling fast.",
                    module="shopping",
                    category_id=cat.id,
                    country="DE", # Simplify
                    city="Berlin",
                    price=price,
                    currency="EUR",
                    user_id=user_id,
                    status="active",
                    images=generate_media(""),
                    image_count=4,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)
                await session.flush() # Get ID

                # Insert Listing Attributes (v2 Typed)
                for key, val in attributes_data.items():
                    if key not in attr_map: continue
                    attr_def = attr_map[key]
                    
                    la = ListingAttribute(
                        listing_id=listing.id,
                        attribute_id=attr_def.id
                    )
                    
                    # Determine value type
                    if attr_def.attribute_type == "select":
                        # Find option ID
                        opts = opt_map.get(key, [])
                        target = next((o for o in opts if o.value == val), None)
                        if target:
                            la.value_option_id = target.id
                    elif attr_def.attribute_type == "boolean":
                        la.value_boolean = bool(val)
                    elif attr_def.attribute_type == "number":
                        la.value_number = val
                    elif attr_def.attribute_type == "text":
                        la.value_text = str(val)
                    
                    session.add(la)

            # 4. Electronics
            cat_phone = get_cat("smartphones")
            if cat_phone:
                brands = ["apple", "samsung", "xiaomi"]
                models = {"apple": ["iPhone 13", "iPhone 14"], "samsung": ["Galaxy S22", "A53"], "xiaomi": ["Redmi Note 11"]}
                
                for _ in range(COUNT_ELEC):
                    brand_val = random.choice(brands)
                    model = random.choice(models[brand_val])
                    storage = random.choice(["128gb", "256gb"])
                    
                    await create_listing(
                        f"{brand_val.title()} {model} {storage.upper()}",
                        cat_phone,
                        random.randint(300, 1200),
                        {
                            "brand_electronics": brand_val,
                            "storage_capacity": storage,
                            "screen_size": 6.1,
                            "condition_shopping": random.choice(["new", "used"]),
                            "shipping_available": True
                        }
                    )

            # 5. Fashion
            cat_shoes = get_cat("shoes")
            if cat_shoes:
                for _ in range(COUNT_FASH):
                    size = random.choice(["40", "41", "42", "43"])
                    color = random.choice(["black", "white"])
                    
                    await create_listing(
                        f"Nike Running Shoes Size {size} {color.title()}",
                        cat_shoes,
                        random.randint(50, 150),
                        {
                            "size_shoes": size,
                            "color": color,
                            "gender": "men",
                            "condition_shopping": "new",
                            "shipping_available": True,
                            "brand_fashion": "Nike"
                        }
                    )

            # 6. Home
            cat_furn = get_cat("furniture")
            if cat_furn:
                for _ in range(COUNT_HOME):
                    material = random.choice(["wood", "metal"])
                    await create_listing(
                        f"Modern {material.title()} Table",
                        cat_furn,
                        random.randint(100, 500),
                        {
                            "material": material,
                            "condition_shopping": "used",
                            "shipping_available": False # Pickup
                        }
                    )

            await session.commit()
            logger.info(f"✅ Created {COUNT_ELEC + COUNT_FASH + COUNT_HOME} Shopping Listings (v6 Typed).")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-prod", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed_shopping_listings_v6())
