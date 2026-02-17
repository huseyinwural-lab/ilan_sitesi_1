import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.vehicle_mdm import VehicleMake, VehicleModel
from app.models.category import Category, CategoryTranslation

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def seed_vehicles():
    print("🚗 Seeding Vehicle Data...")
    
    async with AsyncSessionLocal() as db:
        # 1. Create Category: Vehicles (If not exists)
        # Check root
        stmt = select(Category).where(Category.slug.contains({"en": "vehicle"})) # Simplistic check
        # Better: Check exact match logic from seed_real_estate
        # For this script, assume we just add Makes/Models to MDM
        
        # 2. Seed Makes
        makes_data = ["Audi", "BMW", "Mercedes-Benz", "Volkswagen", "Ford", "Toyota", "Fiat", "Honda"]
        
        make_map = {}
        for m_name in makes_data:
            stmt = select(VehicleMake).where(VehicleMake.name == m_name)
            make = (await db.execute(stmt)).scalar_one_or_none()
            
            if not make:
                make = VehicleMake(name=m_name)
                db.add(make)
                await db.flush()
            
            make_map[m_name] = make.id
            
        # 3. Seed Models (Sample)
        models_data = {
            "Audi": ["A3", "A4", "A6", "Q5", "Q7"],
            "BMW": ["3 Series", "5 Series", "X3", "X5"],
            "Mercedes-Benz": ["C-Class", "E-Class", "S-Class", "GLC"],
            "Volkswagen": ["Golf", "Passat", "Tiguan", "Polo"]
        }
        
        for m_name, models in models_data.items():
            mid = make_map.get(m_name)
            if mid:
                for mod_name in models:
                    stmt = select(VehicleModel).where(VehicleModel.make_id == mid, VehicleModel.name == mod_name)
                    exists = (await db.execute(stmt)).scalar_one_or_none()
                    if not exists:
                        db.add(VehicleModel(make_id=mid, name=mod_name))
                        
        await db.commit()
        print("✅ Vehicle MDM Seeded.")

if __name__ == "__main__":
    asyncio.run(seed_vehicles())
