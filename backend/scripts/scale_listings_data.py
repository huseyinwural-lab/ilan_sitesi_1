
import asyncio
import logging
import sys
import os
import random
import uuid
import copy
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing
from app.models.attribute import ListingAttribute

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scale_data")

TARGET_COUNT = 10000
BATCH_SIZE = 500

async def scale_listings_data():
    is_prod = os.environ.get("APP_ENV") == "production"
    if is_prod and "--allow-prod" not in sys.argv:
        logger.error("🚫 STOP: Production Requires --allow-prod flag.")
        return

    logger.info(f"📈 Starting Data Scale to {TARGET_COUNT} Listings...")

    async with AsyncSessionLocal() as session:
        try:
            # 1. Fetch Source Data (Seed v6)
            # Only fetch Active to clone
            res = await session.execute(select(Listing).where(Listing.status == 'active').limit(500))
            source_listings = res.scalars().all()
            
            if not source_listings:
                logger.error("❌ No source listings found! Run seeds first.")
                return
            
            # Need to fetch attributes for sources too (Lazy load issue if session closed? No, inside context)
            # But better to eager load or fetch manually if we are cloning.
            # ORM clone:
            # ListingAttribute is a separate table.
            # We need to fetch ListingAttributes for these source listings.
            
            source_ids = [l.id for l in source_listings]
            
            # Strategy:
            # Loop TARGET / len(source) times
            multiplier = int(TARGET_COUNT / len(source_listings)) + 1
            logger.info(f"Source size: {len(source_listings)}. Multiplier: {multiplier}x")
            
            total_inserted = 0
            
            for m in range(multiplier):
                if total_inserted >= TARGET_COUNT: break
                
                new_listings = []
                new_attributes = []
                
                for src in source_listings:
                    if total_inserted >= TARGET_COUNT: break
                    
                    # Clone Listing
                    new_id = uuid.uuid4()
                    
                    # Jitter
                    price_jitter = int(src.price * random.uniform(0.9, 1.1)) if src.price else 0
                    date_jitter = datetime.now(timezone.utc) - timedelta(days=random.randint(0, 365))
                    
                    l = Listing(
                        id=new_id,
                        title=f"{src.title} (Copy {m})",
                        description=src.description,
                        module=src.module,
                        category_id=src.category_id,
                        country=src.country,
                        city=src.city,
                        price=price_jitter,
                        currency=src.currency,
                        user_id=src.user_id,
                        dealer_id=src.dealer_id,
                        is_dealer_listing=src.is_dealer_listing,
                        status="active",
                        images=src.images,
                        image_count=src.image_count,
                        attributes=src.attributes, # Legacy JSON
                        created_at=date_jitter,
                        make_id=src.make_id,
                        model_id=src.model_id
                    )
                    new_listings.append(l)
                    
                    # Clone Attributes (Typed)
                    # We need to fetch them from DB for the source listing
                    # Doing this efficiently: Fetch ALL attributes for source batch once, store in map?
                    # Or fetch inside loop (Slow).
                    # Optimization: Before loop, fetch all attributes for source_ids.
                    pass 
                    
                    total_inserted += 1
                
                # Fetch Attributes Map (Once per source batch is simpler, but we iterate multiplier)
                # To be fast:
                # We can reuse the same attribute set structure.
                # Let's fetch attrs for source_listings ONCE outside the loop.
                pass 

                # Bulk Save Listings
                session.add_all(new_listings)
                
                # We need to know which attributes belong to which source to clone them to new_id.
                # Complex with bulk.
                # Simplified: Commit listings first? Or flush.
                # If we do it purely object based, session.add(l) is fine.
                # But we need to add ListingAttribute objects linked to l.id.
                
                # REWORK LOOP for Attribute Cloning
                # 1. Fetch all source attributes
                stmt = select(ListingAttribute).where(ListingAttribute.listing_id.in_(source_ids))
                res_attrs = await session.execute(stmt)
                source_attrs_flat = res_attrs.scalars().all()
                
                # Map listing_id -> list[ListingAttribute]
                attr_map = {}
                for la in source_attrs_flat:
                    if la.listing_id not in attr_map: attr_map[la.listing_id] = []
                    attr_map[la.listing_id].append(la)
                
                # Now attach to new listings
                for l, src in zip(new_listings, source_listings * multiplier): # Zip might mismatch if logic differs
                    # Match by source ID logic?
                    # new_listings generated from source_listings order.
                    # source: src (the original)
                    # new: l
                    
                    # Copy attributes
                    if src.id in attr_map:
                        for src_attr in attr_map[src.id]:
                            new_la = ListingAttribute(
                                listing_id=l.id,
                                attribute_id=src_attr.attribute_id,
                                value_text=src_attr.value_text,
                                value_number=src_attr.value_number,
                                value_boolean=src_attr.value_boolean,
                                value_option_id=src_attr.value_option_id
                            )
                            new_attributes.append(new_la)
                
                session.add_all(new_attributes)
                
                await session.commit()
                logger.info(f"   Batch {m+1}/{multiplier} committed. Total: {total_inserted}")

            logger.info(f"✅ Scale Complete. Total Listings: {total_inserted} + Original")

        except Exception as e:
            logger.error(f"❌ Scale Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(scale_listings_data())
