
import asyncio
import logging
import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.dealer import Dealer, DealerApplication
from app.models.commercial import DealerPackage, DealerSubscription
from app.models.moderation import Listing
from app.models.category import Category
from app.models.billing import Invoice
from app.server import get_password_hash

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dummy_seed")

# CONFIG
COUNT_INDIVIDUAL = 20
COUNT_DEALER = 10
COUNT_LISTINGS = 40
COUNTRIES = ["DE", "TR", "FR"]

async def seed_dummy_data():
    # Safety Guard
    if os.environ.get("APP_ENV") == "production":
        logger.error("🚫 STOP: Cannot run seed in PRODUCTION!")
        return

    logger.info("🌱 Starting Dummy Data Seed...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Cleanup (Optional, but good for idempotent runs in dev)
            # Only delete dummy data, preserve config
            logger.info("Cleaning old dummy data...")
            await session.execute(delete(Listing).where(Listing.title.like("Test %")))
            await session.execute(delete(DealerSubscription)) # Cascades usually, but safe to be explicit
            await session.execute(delete(Dealer)) # Linked to apps
            await session.execute(delete(DealerApplication).where(DealerApplication.company_name.like("Test %")))
            await session.execute(delete(User).where(User.email.like("user_%@example.com")))
            await session.commit()

            # 2. Users (Individual)
            users = []
            for i in range(COUNT_INDIVIDUAL):
                country = random.choices(COUNTRIES, weights=[50, 30, 20])[0]
                user = User(
                    email=f"user_{i}@example.com",
                    hashed_password=get_password_hash("password"),
                    full_name=f"Test User {i}",
                    role="individual",
                    country_scope=[country],
                    is_active=True,
                    is_verified=random.random() < 0.7,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 365))
                )
                session.add(user)
                users.append(user)
            await session.flush()
            logger.info(f"✅ Created {len(users)} Individual Users")

            # 3. Dealers
            dealers = []
            # Ensure Packages Exist (P4 Requirement)
            # We assume seed_production_data created them, or we verify here.
            # Fetch existing packages
            pkg_res = await session.execute(select(DealerPackage))
            packages = pkg_res.scalars().all()
            if not packages:
                logger.warning("⚠️ No Dealer Packages found! Run seed_production_data.py first.")
                return

            tiers = ["STANDARD"] * 6 + ["PREMIUM"] * 3 + ["ENTERPRISE"] * 1
            random.shuffle(tiers)

            for i in range(COUNT_DEALER):
                country = "DE" # Dealers mostly DE for this dataset
                tier = tiers[i]
                
                # Find matching package
                pkg = next((p for p in packages if p.country == country and p.tier == tier), packages[0])

                # Create User for Dealer
                dealer_user = User(
                    email=f"dealer_{i}@example.com",
                    hashed_password=get_password_hash("password"),
                    full_name=f"Dealer Owner {i}",
                    role="dealer",
                    country_scope=[country],
                    is_active=True,
                    is_verified=True
                )
                session.add(dealer_user)
                await session.flush()

                # Application
                app = DealerApplication(
                    country=country,
                    dealer_type="auto_dealer" if i < 5 else "real_estate_agency",
                    company_name=f"Test Dealer {i} ({tier})",
                    contact_name=dealer_user.full_name,
                    contact_email=dealer_user.email,
                    status="approved"
                )
                session.add(app)
                await session.flush()

                # Dealer
                dealer = Dealer(
                    id=uuid.uuid4(),
                    application_id=app.id,
                    country=country,
                    dealer_type=app.dealer_type,
                    company_name=app.company_name,
                    is_active=True
                )
                session.add(dealer)
                dealers.append(dealer)
                await session.flush()

                # Subscription
                inv = Invoice(
                    invoice_no=f"INV-DUMMY-{i}",
                    country=country,
                    currency=pkg.currency,
                    customer_type="dealer",
                    customer_ref_id=dealer.id,
                    customer_name=dealer.company_name,
                    status="paid",
                    gross_total=pkg.price_net,
                    net_total=pkg.price_net,
                    tax_total=0,
                    tax_rate_snapshot=0
                )
                session.add(inv)
                await session.flush()

                sub = DealerSubscription(
                    dealer_id=dealer.id,
                    package_id=pkg.id,
                    invoice_id=inv.id,
                    start_at=datetime.now(timezone.utc),
                    end_at=datetime.now(timezone.utc) + timedelta(days=30),
                    status="active",
                    included_listing_quota=pkg.listing_limit,
                    used_listing_quota=random.randint(0, int(pkg.listing_limit / 2))
                )
                session.add(sub)

            await session.flush()
            logger.info(f"✅ Created {len(dealers)} Dealers with Subscriptions")

            # 4. Listings
            # Get Categories
            cat_res = await session.execute(select(Category))
            cats = cat_res.scalars().all()
            if not cats:
                logger.warning("⚠️ No Categories found!")
                return

            for i in range(COUNT_LISTINGS):
                # Random Owner (Dealer or User)
                if random.random() < 0.7:
                    owner_dealer = random.choice(dealers)
                    owner_user_id = uuid.uuid4() # Mock, or fetch user linked to dealer if we had link
                    # In our model, Dealer doesn't have direct User link in this script scope easily accessible
                    # So we pick a random user for user_id, but assign dealer_id
                    # This is fine for listing display.
                    owner_user = random.choice(users) # Just for FK
                else:
                    owner_dealer = None
                    owner_user = random.choice(users)

                status_pool = ["active"] * 60 + ["pending"] * 25 + ["rejected"] * 15
                status = random.choice(status_pool)
                
                cat = random.choice(cats)
                
                listing = Listing(
                    title=f"Test Listing {i} - {cat.slug['en']}",
                    description="This is a generated dummy listing for testing purposes.",
                    module=cat.module,
                    country=random.choice(COUNTRIES),
                    price=random.randint(1000, 500000),
                    currency="EUR",
                    user_id=owner_user.id,
                    dealer_id=owner_dealer.id if owner_dealer else None,
                    is_dealer_listing=bool(owner_dealer),
                    status=status,
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(0, 30))
                )
                session.add(listing)

            await session.commit()
            logger.info(f"✅ Created {COUNT_LISTINGS} Listings")
            logger.info("🎉 Seed Complete!")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_dummy_data())
