
import asyncio
import logging
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.attribute import Attribute, AttributeOption
from app.models.vehicle_mdm import VehicleMake

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_options")

async def seed_options():
    logger.info("🎨 Seeding Vehicle Attribute Options...")
    
    options_data = {
        "fuel_type": [
            {"value": "gasoline", "label": {"en": "Gasoline", "tr": "Benzin", "de": "Benzin"}},
            {"value": "diesel", "label": {"en": "Diesel", "tr": "Dizel", "de": "Diesel"}},
            {"value": "electric", "label": {"en": "Electric", "tr": "Elektrik", "de": "Elektro"}},
            {"value": "hybrid", "label": {"en": "Hybrid", "tr": "Hibrit", "de": "Hybrid"}},
            {"value": "lpg", "label": {"en": "LPG", "tr": "LPG", "de": "Autogas"}}
        ],
        "gear_type": [
            {"value": "manual", "label": {"en": "Manual", "tr": "Manuel", "de": "Schaltgetriebe"}},
            {"value": "automatic", "label": {"en": "Automatic", "tr": "Otomatik", "de": "Automatik"}},
            {"value": "semi", "label": {"en": "Semi-Automatic", "tr": "Yarı Otomatik", "de": "Halbautomatik"}}
        ],
        "body_type": [
            {"value": "sedan", "label": {"en": "Sedan", "tr": "Sedan", "de": "Limousine"}},
            {"value": "hatchback", "label": {"en": "Hatchback", "tr": "Hatchback", "de": "Kleinwagen"}},
            {"value": "suv", "label": {"en": "SUV", "tr": "SUV", "de": "Geländewagen"}},
            {"value": "station", "label": {"en": "Station Wagon", "tr": "Station Wagon", "de": "Kombi"}},
            {"value": "coupe", "label": {"en": "Coupe", "tr": "Coupe", "de": "Coupé"}},
            {"value": "convertible", "label": {"en": "Convertible", "tr": "Cabrio", "de": "Cabrio"}},
            {"value": "van", "label": {"en": "Van", "tr": "Minivan", "de": "Van"}}
        ],
        "condition": [
             {"value": "new", "label": {"en": "New", "tr": "Sıfır", "de": "Neu"}},
             {"value": "used", "label": {"en": "Used", "tr": "İkinci El", "de": "Gebraucht"}},
             {"value": "damaged", "label": {"en": "Damaged", "tr": "Hasarlı", "de": "Beschädigt"}}
        ],
        "drive_train": [
            {"value": "fwd", "label": {"en": "Front Wheel Drive", "tr": "Önden Çekiş", "de": "Vorderradantrieb"}},
            {"value": "rwd", "label": {"en": "Rear Wheel Drive", "tr": "Arkadan İtiş", "de": "Hinterradantrieb"}},
            {"value": "4wd", "label": {"en": "4WD", "tr": "4 Çeker", "de": "Allrad"}}
        ],
        "emission_class": [
            {"value": "euro6", "label": {"en": "Euro 6", "tr": "Euro 6", "de": "Euro 6"}},
            {"value": "euro5", "label": {"en": "Euro 5", "tr": "Euro 5", "de": "Euro 5"}},
            {"value": "euro4", "label": {"en": "Euro 4", "tr": "Euro 4", "de": "Euro 4"}}
        ],
        "air_condition": [
            {"value": "auto", "label": {"en": "Automatic AC", "tr": "Dijital Klima", "de": "Klimaautomatik"}},
            {"value": "manual", "label": {"en": "Manual AC", "tr": "Manuel Klima", "de": "Klimaanlage"}},
            {"value": "none", "label": {"en": "None", "tr": "Yok", "de": "Keine"}}
        ],
        "moto_type": [
            {"value": "scooter", "label": {"en": "Scooter", "tr": "Scooter", "de": "Roller"}},
            {"value": "racing", "label": {"en": "Racing", "tr": "Racing", "de": "Sportler"}},
            {"value": "chopper", "label": {"en": "Chopper", "tr": "Chopper", "de": "Chopper"}},
            {"value": "naked", "label": {"en": "Naked", "tr": "Naked", "de": "Naked Bike"}},
            {"value": "touring", "label": {"en": "Touring", "tr": "Touring", "de": "Tourer"}}
        ],
        "comm_vehicle_type": [
            {"value": "van", "label": {"en": "Panel Van", "tr": "Panelvan", "de": "Kastenwagen"}},
            {"value": "truck", "label": {"en": "Truck", "tr": "Kamyon", "de": "Lkw"}},
            {"value": "bus", "label": {"en": "Bus", "tr": "Otobüs", "de": "Bus"}}
        ],
        "box_type": [
             {"value": "closed", "label": {"en": "Closed Box", "tr": "Kapalı Kasa", "de": "Koffer"}},
             {"value": "open", "label": {"en": "Open Box", "tr": "Açık Kasa", "de": "Pritsche"}},
             {"value": "frigo", "label": {"en": "Refrigerated", "tr": "Frigofirik", "de": "Kühlkoffer"}}
        ]
    }

    async with AsyncSessionLocal() as session:
        # 1. Standard Options
        for key, opts in options_data.items():
            res = await session.execute(select(Attribute).where(Attribute.key == key))
            attr = res.scalar_one_or_none()
            
            if not attr:
                logger.warning(f"⚠️ Attribute {key} not found. Skipping options.")
                continue
                
            for i, opt in enumerate(opts):
                res_opt = await session.execute(select(AttributeOption).where(
                    AttributeOption.attribute_id == attr.id,
                    AttributeOption.value == opt["value"]
                ))
                if not res_opt.scalar_one_or_none():
                    new_opt = AttributeOption(
                        attribute_id=attr.id,
                        value=opt["value"],
                        label=opt["label"],
                        sort_order=i
                    )
                    session.add(new_opt)
        
        # 2. Sync Brand Options from VehicleMake
        logger.info("Syncing Brand Options...")
        res_brand = await session.execute(select(Attribute).where(Attribute.key == 'brand'))
        attr_brand = res_brand.scalar_one_or_none()
        
        if attr_brand:
            makes = (await session.execute(select(VehicleMake))).scalars().all()
            for i, make in enumerate(makes):
                # Check if option exists
                res_opt = await session.execute(select(AttributeOption).where(
                    AttributeOption.attribute_id == attr_brand.id,
                    AttributeOption.value == make.slug
                ))
                if not res_opt.scalar_one_or_none():
                    new_opt = AttributeOption(
                        attribute_id=attr_brand.id,
                        value=make.slug,
                        label={"en": make.name, "tr": make.name, "de": make.name}, # Using name for all langs
                        sort_order=i
                    )
                    session.add(new_opt)

        await session.commit()
        logger.info("✅ Options Seeded (including Brands).")

if __name__ == "__main__":
    asyncio.run(seed_options())
