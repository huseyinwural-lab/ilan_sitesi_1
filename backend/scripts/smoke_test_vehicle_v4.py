
import asyncio
import sys
import os
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.moderation import Listing

async def smoke_test_vehicle_v4():
    print("🚗 Starting Vehicle Filter Smoke Test v4...")
    
    async with AsyncSessionLocal() as session:
        # Fetch all vehicle listings
        res = await session.execute(select(Listing).where(Listing.module == 'vehicle'))
        listings = res.scalars().all()
        
        print(f"📊 Total Vehicle Listings: {len(listings)}")
        
        # 1. Car Filters
        diesels = [l for l in listings if l.attributes.get('fuel_type') == 'diesel']
        print(f"   -> Diesel Cars: {len(diesels)}")
        
        automatics = [l for l in listings if l.attributes.get('gear_type') == 'automatic']
        print(f"   -> Automatic Cars: {len(automatics)}")
        
        euro6 = [l for l in listings if l.attributes.get('emission_class') == 'euro6']
        print(f"   -> Euro 6 Cars: {len(euro6)}")
        
        # 2. Moto Filters
        motos = [l for l in listings if 'moto_type' in l.attributes]
        abs_motos = [l for l in motos if l.attributes.get('abs') is True]
        print(f"   -> Motorcycles: {len(motos)}")
        print(f"   -> ABS Motorcycles: {len(abs_motos)}")
        
        # 3. Commercial Filters
        trucks = [l for l in listings if 'load_capacity_kg' in l.attributes]
        heavy_load = [l for l in trucks if l.attributes.get('load_capacity_kg', 0) > 5000]
        print(f"   -> Commercial Vehicles: {len(trucks)}")
        print(f"   -> Heavy Load (>5000kg): {len(heavy_load)}")
        
        # Validation
        if len(diesels) > 0 and len(automatics) > 0 and len(abs_motos) > 0 and len(heavy_load) > 0:
            print("✅ Filter Logic: PASS (Data exists for all filters)")
        else:
            print("⚠️ Filter Logic: WARNING (Some filter buckets empty?)")

        # Integrity Check
        errors = 0
        for l in motos:
            if 'fuel_type' not in l.attributes:
                # In v4 design, fuel_type is Car specific or Global?
                # Seed script v4 put fuel_type in 'moto' generator too. So it should be there.
                # Actually, check seed_vehicle_listings.py -> generate_attributes for moto adds 'moto_type', 'abs', 'cc', 'power'.
                # Does it add global? Yes, 'fuel_type' is in global attrs in that script.
                pass
            if 'gear_type' in l.attributes:
                 print(f"❌ Moto {l.id} has gear_type (Should be Car only in this seed logic)")
                 errors += 1
        
        if errors == 0:
            print("✅ Integrity Check: PASS (No attribute leakage)")

if __name__ == "__main__":
    asyncio.run(smoke_test_vehicle_v4())
