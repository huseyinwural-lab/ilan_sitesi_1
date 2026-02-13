
import asyncio
import logging
import sys
import os
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.vehicle_mdm import VehicleMake, VehicleModel

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_vehicle_mdm")

async def seed_vehicle_master_data():
    logger.info("🚗 Starting Vehicle Master Data Seed (v1)...")
    
    # Provider Data (Simulated JSON Source)
    # Top Brands for EU Market
    provider_data = [
        {
            "name": "BMW", "slug": "bmw", "types": ["car", "moto"],
            "models": [
                {"name": "3 Series", "slug": "3-series", "type": "car"},
                {"name": "5 Series", "slug": "5-series", "type": "car"},
                {"name": "X5", "slug": "x5", "type": "car"},
                {"name": "iX", "slug": "ix", "type": "car"},
                {"name": "R 1250 GS", "slug": "r-1250-gs", "type": "moto"}
            ]
        },
        {
            "name": "Mercedes-Benz", "slug": "mercedes-benz", "types": ["car", "comm"],
            "models": [
                {"name": "C-Class", "slug": "c-class", "type": "car"},
                {"name": "E-Class", "slug": "e-class", "type": "car"},
                {"name": "Sprinter", "slug": "sprinter", "type": "comm"},
                {"name": "Vito", "slug": "vito", "type": "comm"}
            ]
        },
        {
            "name": "Volkswagen", "slug": "vw", "types": ["car", "comm"],
            "models": [
                {"name": "Golf", "slug": "golf", "type": "car"},
                {"name": "Passat", "slug": "passat", "type": "car"},
                {"name": "Transporter", "slug": "transporter", "type": "comm"}
            ]
        },
        {
            "name": "Audi", "slug": "audi", "types": ["car"],
            "models": [
                {"name": "A3", "slug": "a3", "type": "car"},
                {"name": "A4", "slug": "a4", "type": "car"},
                {"name": "Q7", "slug": "q7", "type": "car"}
            ]
        },
        {
            "name": "Tesla", "slug": "tesla", "types": ["car"],
            "models": [
                {"name": "Model 3", "slug": "model-3", "type": "car"},
                {"name": "Model Y", "slug": "model-y", "type": "car"}
            ]
        },
        {
            "name": "Renault", "slug": "renault", "types": ["car", "comm"],
            "models": [
                {"name": "Clio", "slug": "clio", "type": "car"},
                {"name": "Megane", "slug": "megane", "type": "car"},
                {"name": "Master", "slug": "master", "type": "comm"}
            ]
        },
        {
            "name": "Ford", "slug": "ford", "types": ["car", "comm"],
            "models": [
                {"name": "Focus", "slug": "focus", "type": "car"},
                {"name": "Transit", "slug": "transit", "type": "comm"}
            ]
        },
        {
            "name": "Yamaha", "slug": "yamaha", "types": ["moto"],
            "models": [
                {"name": "MT-07", "slug": "mt-07", "type": "moto"},
                {"name": "YZF-R1", "slug": "yzf-r1", "type": "moto"}
            ]
        },
        {
            "name": "Honda", "slug": "honda", "types": ["car", "moto"],
            "models": [
                {"name": "Civic", "slug": "civic", "type": "car"},
                {"name": "CBR1000RR", "slug": "cbr1000rr", "type": "moto"}
            ]
        },
        {
            "name": "Togg", "slug": "togg", "types": ["car"],
            "models": [
                {"name": "T10X", "slug": "t10x", "type": "car"}
            ]
        }
    ]

    async with AsyncSessionLocal() as session:
        try:
            for make_data in provider_data:
                # Upsert Make
                res = await session.execute(select(VehicleMake).where(VehicleMake.slug == make_data["slug"]))
                make = res.scalar_one_or_none()
                
                if not make:
                    make = VehicleMake(
                        slug=make_data["slug"],
                        name=make_data["name"],
                        vehicle_types=make_data["types"],
                        source="manual_seed_v1"
                    )
                    session.add(make)
                    await session.flush()
                    logger.info(f"✅ Created Make: {make.name}")
                
                # Upsert Models
                for model_data in make_data["models"]:
                    m_res = await session.execute(select(VehicleModel).where(
                        VehicleModel.make_id == make.id,
                        VehicleModel.slug == model_data["slug"]
                    ))
                    model = m_res.scalar_one_or_none()
                    
                    if not model:
                        model = VehicleModel(
                            make_id=make.id,
                            slug=model_data["slug"],
                            name=model_data["name"],
                            vehicle_type=model_data["type"]
                        )
                        session.add(model)
            
            await session.commit()
            logger.info("🎉 Vehicle Master Data Seed Complete.")

        except Exception as e:
            logger.error(f"❌ Seed Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_vehicle_master_data())
