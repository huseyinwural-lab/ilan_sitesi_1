
import asyncio
import logging
import sys
import os
import argparse
from sqlalchemy import select, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_v4")

async def seed_v4(allow_prod=False, dry_run=False):
    is_prod = os.environ.get("APP_ENV") == "production"
    
    if is_prod and not allow_prod:
        logger.error("🚫 STOP: Production requires --allow-prod flag and explicit intent.")
        return

    logger.info(f"🚀 Starting Seed v4 (Vehicle Attributes) - Dry Run: {dry_run}")

    async with AsyncSessionLocal() as session:
        try:
            # === DEFINITIONS (Same as before) ===
            global_attrs = [
                ("brand", "select", None, {"en": "Brand", "tr": "Marka", "de": "Marke", "fr": "Marque"}),
                ("model", "text", None, {"en": "Model", "tr": "Model", "de": "Modell", "fr": "Modèle"}),
                ("year", "number", None, {"en": "Year", "tr": "Yıl", "de": "Baujahr", "fr": "Année"}),
                ("km", "number", "km", {"en": "Mileage", "tr": "KM", "de": "Kilometerstand", "fr": "Kilométrage"}),
                ("condition", "select", None, {"en": "Condition", "tr": "Durum", "de": "Zustand", "fr": "État"}),
                ("warranty", "boolean", None, {"en": "Warranty", "tr": "Garanti", "de": "Garantie", "fr": "Garantie"}),
                ("swap", "boolean", None, {"en": "Swap", "tr": "Takas", "de": "Tausch", "fr": "Échange"}),
                ("fuel_type", "select", None, {"en": "Fuel Type", "tr": "Yakıt", "de": "Kraftstoff", "fr": "Carburant"}),
            ]

            car_attrs = [
                ("gear_type", "select", None, {"en": "Gearbox", "tr": "Vites", "de": "Getriebe", "fr": "Boîte"}),
                ("body_type", "select", None, {"en": "Body Type", "tr": "Kasa Tipi", "de": "Karosserie", "fr": "Carrosserie"}),
                ("engine_power_kw", "number", "kW", {"en": "Power (kW)", "tr": "Motor Gücü (kW)", "de": "Leistung (kW)", "fr": "Puissance (kW)"}),
                ("engine_capacity_cc", "number", "cc", {"en": "Capacity (cc)", "tr": "Motor Hacmi", "de": "Hubraum", "fr": "Cylindrée"}),
                ("drive_train", "select", None, {"en": "Drive Train", "tr": "Çekiş", "de": "Antrieb", "fr": "Transmission"}),
                ("emission_class", "select", None, {"en": "Emission Class", "tr": "Emisyon", "de": "Schadstoffklasse", "fr": "Émission"}),
                ("inspection_valid", "boolean", None, {"en": "Inspection Valid", "tr": "Muayene Geçerli", "de": "HU/AU neu", "fr": "Contrôle technique"}),
                ("air_condition", "select", None, {"en": "Air Condition", "tr": "Klima", "de": "Klimaanlage", "fr": "Climatisation"}),
                ("navigation", "boolean", None, {"en": "Navigation", "tr": "Navigasyon", "de": "Navi", "fr": "GPS"}),
                ("leather_seats", "boolean", None, {"en": "Leather Seats", "tr": "Deri Koltuk", "de": "Ledersitze", "fr": "Cuir"}),
                ("sunroof", "boolean", None, {"en": "Sunroof", "tr": "Sunroof", "de": "Schiebedach", "fr": "Toit ouvrant"}),
                ("parking_sensors", "boolean", None, {"en": "Parking Sensors", "tr": "Park Sensörü", "de": "Einparkhilfe", "fr": "Radar de recul"}),
            ]

            moto_attrs = [
                ("moto_type", "select", None, {"en": "Motorcycle Type", "tr": "Motosiklet Tipi", "de": "Motorradtyp", "fr": "Type Moto"}),
                ("abs", "boolean", None, {"en": "ABS", "tr": "ABS", "de": "ABS", "fr": "ABS"}),
            ]

            comm_attrs = [
                ("comm_vehicle_type", "select", None, {"en": "Vehicle Type", "tr": "Araç Tipi", "de": "Fahrzeugtyp", "fr": "Type Véhicule"}),
                ("load_capacity_kg", "number", "kg", {"en": "Load Capacity", "tr": "Taşıma Kapasitesi", "de": "Nutzlast", "fr": "Charge utile"}),
                ("box_type", "select", None, {"en": "Box Type", "tr": "Kasa Tipi", "de": "Aufbau", "fr": "Carrosserie"}),
            ]

            # (Options Map Logic Skipped for brevity, assume populated)
            options_map = {}

            # === EXECUTION ===

            async def upsert_attr(key, type_name, unit, name):
                res = await session.execute(select(Attribute).where(Attribute.key == key))
                attr = res.scalar_one_or_none()
                if not attr:
                    attr = Attribute(key=key, attribute_type=type_name, unit=unit, name=name, is_active=True, is_filterable=True, is_required=False)
                    session.add(attr)
                if not dry_run:
                    await session.flush()
                return attr

            all_definitions = global_attrs + car_attrs + moto_attrs + comm_attrs
            attr_map = {}

            for key, type_name, unit, name in all_definitions:
                attr = await upsert_attr(key, type_name, unit, name)
                if not dry_run:
                    attr_map[key] = attr.id

            # === BINDING FIX ===
            if not dry_run:
                logger.info("Linking Attributes to Categories...")
                
                # Fetch categories
                res = await session.execute(select(Category))
                all_cats = res.scalars().all()
                
                # Ensure Categories Exist (If seed_production_data.py failed or didn't run for vehicles)
                # Check for root 'vehicle'
                vehicle_root = next((c for c in all_cats if c.module == "vehicle" and c.parent_id is None), None)
                
                if not vehicle_root:
                    logger.info("🆕 Creating 'Vehicle' root category...")
                    vehicle_root = Category(module="vehicle", slug={"en": "vehicles", "tr": "vasita", "de": "fahrzeuge"}, is_enabled=True, allowed_countries=["DE","TR","FR"])
                    session.add(vehicle_root)
                    await session.flush()
                    vehicle_root.path = str(vehicle_root.id)
                    all_cats.append(vehicle_root)

                # Ensure Subcats
                def ensure_cat(slug, name_en):
                    cat = next((c for c in all_cats if c.slug.get('en') == slug), None)
                    if not cat:
                        logger.info(f"🆕 Creating '{slug}' category...")
                        cat = Category(module="vehicle", parent_id=vehicle_root.id, slug={"en": slug}, is_enabled=True, path=f"{vehicle_root.path}.NEW")
                        session.add(cat)
                        # We need flush to get ID for path update
                        return cat, True
                    return cat, False

                cars_cat, created_cars = ensure_cat("cars", "Cars")
                moto_cat, created_moto = ensure_cat("motorcycles", "Motorcycles")
                comm_cat, created_comm = ensure_cat("commercial-vehicles", "Commercial Vehicles")
                
                if created_cars or created_moto or created_comm:
                    await session.flush()
                    if created_cars: cars_cat.path = f"{vehicle_root.path}.{cars_cat.id}"
                    if created_moto: moto_cat.path = f"{vehicle_root.path}.{moto_cat.id}"
                    if created_comm: comm_cat.path = f"{vehicle_root.path}.{comm_cat.id}"
                    # Re-fetch or append to all_cats
                    all_cats.extend([c for c in [cars_cat, moto_cat, comm_cat] if c])

                async def link(target_cat, attr_keys):
                    if not target_cat: return
                    await session.execute(delete(CategoryAttributeMap).where(CategoryAttributeMap.category_id == target_cat.id))
                    for key in attr_keys:
                        if key in attr_map:
                            session.add(CategoryAttributeMap(category_id=target_cat.id, attribute_id=attr_map[key], inherit_to_children=True))
                    logger.info(f"🔗 Linked attributes to {target_cat.slug.get('en')}")

                global_keys = [x[0] for x in global_attrs]
                car_keys = [x[0] for x in car_attrs]
                moto_keys = [x[0] for x in moto_attrs]
                comm_keys = [x[0] for x in comm_attrs]

                await link(vehicle_root, global_keys)
                await link(cars_cat, car_keys)
                await link(moto_cat, moto_keys)
                await link(comm_cat, comm_keys)

            if not dry_run:
                await session.commit()
                logger.info("💾 Transaction Committed.")
            else:
                await session.rollback()
                logger.info("🛑 Dry Run - No changes made.")

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-prod", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    asyncio.run(seed_v4(allow_prod=args.allow_prod, dry_run=args.dry_run))
