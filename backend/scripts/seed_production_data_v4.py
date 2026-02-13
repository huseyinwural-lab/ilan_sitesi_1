
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
            # === DEFINITIONS ===
            
            # 1. GLOBAL ATTRIBUTES (Vehicle Root)
            global_attrs = [
                ("brand", "select", None, {"en": "Brand", "tr": "Marka", "de": "Marke", "fr": "Marque"}),
                ("model", "text", None, {"en": "Model", "tr": "Model", "de": "Modell", "fr": "Modèle"}),
                ("year", "number", None, {"en": "Year", "tr": "Yıl", "de": "Baujahr", "fr": "Année"}),
                ("km", "number", "km", {"en": "Mileage", "tr": "KM", "de": "Kilometerstand", "fr": "Kilométrage"}),
                ("condition", "select", None, {"en": "Condition", "tr": "Durum", "de": "Zustand", "fr": "État"}),
                ("warranty", "boolean", None, {"en": "Warranty", "tr": "Garanti", "de": "Garantie", "fr": "Garantie"}),
                ("swap", "boolean", None, {"en": "Swap", "tr": "Takas", "de": "Tausch", "fr": "Échange"}),
                ("fuel_type", "select", None, {"en": "Fuel Type", "tr": "Yakıt", "de": "Kraftstoff", "fr": "Carburant"}), # Global for all vehicles
            ]

            # 2. CAR ATTRIBUTES
            car_attrs = [
                ("gear_type", "select", None, {"en": "Gearbox", "tr": "Vites", "de": "Getriebe", "fr": "Boîte"}),
                ("body_type", "select", None, {"en": "Body Type", "tr": "Kasa Tipi", "de": "Karosserie", "fr": "Carrosserie"}),
                ("engine_power_kw", "number", "kW", {"en": "Power (kW)", "tr": "Motor Gücü (kW)", "de": "Leistung (kW)", "fr": "Puissance (kW)"}),
                ("engine_capacity_cc", "number", "cc", {"en": "Capacity (cc)", "tr": "Motor Hacmi", "de": "Hubraum", "fr": "Cylindrée"}),
                ("drive_train", "select", None, {"en": "Drive Train", "tr": "Çekiş", "de": "Antrieb", "fr": "Transmission"}),
                ("emission_class", "select", None, {"en": "Emission Class", "tr": "Emisyon", "de": "Schadstoffklasse", "fr": "Émission"}),
                ("inspection_valid", "boolean", None, {"en": "Inspection Valid", "tr": "Muayene Geçerli", "de": "HU/AU neu", "fr": "Contrôle technique"}),
                # Equipment
                ("air_condition", "select", None, {"en": "Air Condition", "tr": "Klima", "de": "Klimaanlage", "fr": "Climatisation"}),
                ("navigation", "boolean", None, {"en": "Navigation", "tr": "Navigasyon", "de": "Navi", "fr": "GPS"}),
                ("leather_seats", "boolean", None, {"en": "Leather Seats", "tr": "Deri Koltuk", "de": "Ledersitze", "fr": "Cuir"}),
                ("sunroof", "boolean", None, {"en": "Sunroof", "tr": "Sunroof", "de": "Schiebedach", "fr": "Toit ouvrant"}),
                ("parking_sensors", "boolean", None, {"en": "Parking Sensors", "tr": "Park Sensörü", "de": "Einparkhilfe", "fr": "Radar de recul"}),
            ]

            # 3. MOTO ATTRIBUTES
            moto_attrs = [
                ("moto_type", "select", None, {"en": "Motorcycle Type", "tr": "Motosiklet Tipi", "de": "Motorradtyp", "fr": "Type Moto"}),
                ("abs", "boolean", None, {"en": "ABS", "tr": "ABS", "de": "ABS", "fr": "ABS"}),
            ]

            # 4. COMM ATTRIBUTES
            comm_attrs = [
                ("comm_vehicle_type", "select", None, {"en": "Vehicle Type", "tr": "Araç Tipi", "de": "Fahrzeugtyp", "fr": "Type Véhicule"}),
                ("load_capacity_kg", "number", "kg", {"en": "Load Capacity", "tr": "Taşıma Kapasitesi", "de": "Nutzlast", "fr": "Charge utile"}),
                ("box_type", "select", None, {"en": "Box Type", "tr": "Kasa Tipi", "de": "Aufbau", "fr": "Carrosserie"}),
            ]

            # 5. OPTIONS
            options_map = {
                "brand": [ # Simplified List
                    ("bmw", {"en": "BMW"}), ("mercedes", {"en": "Mercedes-Benz"}), 
                    ("audi", {"en": "Audi"}), ("vw", {"en": "Volkswagen"}), 
                    ("tesla", {"en": "Tesla"}), ("toyota", {"en": "Toyota"}),
                    ("honda", {"en": "Honda"}), ("yamaha", {"en": "Yamaha"}),
                    ("ford", {"en": "Ford"}), ("renault", {"en": "Renault"}),
                ],
                "condition": [
                    ("new", {"en": "New", "tr": "Sıfır", "de": "Neu", "fr": "Neuf"}),
                    ("used", {"en": "Used", "tr": "İkinci El", "de": "Gebraucht", "fr": "Occasion"}),
                    ("classic", {"en": "Classic", "tr": "Klasik", "de": "Oldtimer", "fr": "Collection"}),
                    ("damaged", {"en": "Damaged", "tr": "Hasarlı", "de": "Beschädigt", "fr": "Accidenté"}),
                ],
                "fuel_type": [
                    ("gasoline", {"en": "Petrol", "tr": "Benzin", "de": "Benzin", "fr": "Essence"}),
                    ("diesel", {"en": "Diesel", "tr": "Dizel", "de": "Diesel", "fr": "Diesel"}),
                    ("hybrid", {"en": "Hybrid", "tr": "Hibrit", "de": "Hybrid", "fr": "Hybride"}),
                    ("electric", {"en": "Electric", "tr": "Elektrik", "de": "Elektro", "fr": "Électrique"}),
                    ("lpg", {"en": "LPG", "tr": "LPG", "de": "Autogas", "fr": "GPL"}),
                ],
                "gear_type": [
                    ("manual", {"en": "Manual", "tr": "Manuel", "de": "Schaltgetriebe", "fr": "Manuelle"}),
                    ("automatic", {"en": "Automatic", "tr": "Otomatik", "de": "Automatik", "fr": "Automatique"}),
                    ("semi", {"en": "Semi-Auto", "tr": "Yarı Otomatik", "de": "Halbautomatik", "fr": "Semi-auto"}),
                ],
                "body_type": [
                    ("sedan", {"en": "Sedan", "tr": "Sedan", "de": "Limousine", "fr": "Berline"}),
                    ("suv", {"en": "SUV", "tr": "SUV", "de": "Geländewagen", "fr": "SUV"}),
                    ("hatchback", {"en": "Hatchback", "tr": "Hatchback", "de": "Kleinwagen", "fr": "Hayon"}),
                    ("station", {"en": "Station Wagon", "tr": "Station", "de": "Kombi", "fr": "Break"}),
                    ("coupe", {"en": "Coupe", "tr": "Coupe", "de": "Coupé", "fr": "Coupé"}),
                    ("cabrio", {"en": "Convertible", "tr": "Cabrio", "de": "Cabrio", "fr": "Cabriolet"}),
                ],
                "drive_train": [
                    ("fwd", {"en": "Front Wheel", "tr": "Önden Çekiş", "de": "Frontantrieb", "fr": "Traction"}),
                    ("rwd", {"en": "Rear Wheel", "tr": "Arkadan İtiş", "de": "Heckantrieb", "fr": "Propulsion"}),
                    ("4wd", {"en": "4WD / AWD", "tr": "4x4", "de": "Allrad", "fr": "4x4"}),
                ],
                "emission_class": [
                    ("euro6", {"en": "Euro 6"}), ("euro5", {"en": "Euro 5"}), 
                    ("euro4", {"en": "Euro 4"}), ("euro3", {"en": "Euro 3"}),
                ],
                "air_condition": [
                    ("none", {"en": "None", "tr": "Yok", "de": "Keine", "fr": "Aucune"}),
                    ("manual", {"en": "Manual", "tr": "Manuel", "de": "Klimaanlage", "fr": "Manuelle"}),
                    ("auto", {"en": "Automatic", "tr": "Dijital", "de": "Klimaautomatik", "fr": "Automatique"}),
                ],
                "moto_type": [
                    ("scooter", {"en": "Scooter", "tr": "Scooter", "de": "Roller", "fr": "Scooter"}),
                    ("racing", {"en": "Racing", "tr": "Racing", "de": "Sportler", "fr": "Sportive"}),
                    ("chopper", {"en": "Chopper", "tr": "Chopper", "de": "Chopper", "fr": "Custom"}),
                    ("cross", {"en": "Cross", "tr": "Cross", "de": "Enduro", "fr": "Cross"}),
                    ("naked", {"en": "Naked", "tr": "Naked", "de": "Naked Bike", "fr": "Roadster"}),
                ],
                "comm_vehicle_type": [
                    ("van", {"en": "Van", "tr": "Panelvan", "de": "Kastenwagen", "fr": "Fourgon"}),
                    ("truck", {"en": "Truck", "tr": "Kamyon", "de": "LKW", "fr": "Camion"}),
                    ("bus", {"en": "Bus", "tr": "Otobüs", "de": "Bus", "fr": "Bus"}),
                ],
                "box_type": [
                    ("closed", {"en": "Closed Box", "tr": "Kapalı Kasa", "de": "Koffer", "fr": "Fourgon"}),
                    ("open", {"en": "Open Bed", "tr": "Açık Kasa", "de": "Pritsche", "fr": "Plateau"}),
                    ("frigo", {"en": "Refrigerated", "tr": "Frigo", "de": "Kühlkoffer", "fr": "Frigorifique"}),
                ]
            }

            # === EXECUTION ===

            async def upsert_attr(key, type_name, unit, name):
                res = await session.execute(select(Attribute).where(Attribute.key == key))
                attr = res.scalar_one_or_none()
                
                if attr:
                    logger.info(f"🔹 Update Attribute: {key}")
                    attr.name = name
                    attr.attribute_type = type_name
                    attr.unit = unit
                else:
                    logger.info(f"✅ Create Attribute: {key}")
                    attr = Attribute(
                        key=key,
                        attribute_type=type_name,
                        unit=unit,
                        name=name,
                        is_active=True,
                        is_filterable=True,
                        is_required=False
                    )
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
                    if key in options_map:
                        await session.execute(delete(AttributeOption).where(AttributeOption.attribute_id == attr.id))
                        for idx, (val, label) in enumerate(options_map[key]):
                            session.add(AttributeOption(
                                attribute_id=attr.id,
                                value=val,
                                label=label,
                                sort_order=idx
                            ))

            # === BINDING ===
            if not dry_run:
                logger.info("Linking Attributes to Categories...")
                
                res = await session.execute(select(Category))
                all_cats = res.scalars().all()
                
                # Check/Create Commercial Vehicle Category if missing
                # v1 seed had 'vehicle' -> 'cars', 'motorcycles'.
                # We need 'commercial-vehicles' under 'vehicle' or parallel?
                # Usually parallel module or subcat. Let's assume subcat of 'vehicle' for now to keep module count low.
                
                vehicle_root = next((c for c in all_cats if c.module == "vehicle" and c.parent_id is None), None)
                if vehicle_root:
                    comm_veh_cat = next((c for c in all_cats if c.slug.get('en') == 'commercial-vehicles'), None)
                    if not comm_veh_cat:
                        logger.info("🆕 Creating 'Commercial Vehicles' category...")
                        comm_veh_cat = Category(
                            module="vehicle",
                            parent_id=vehicle_root.id,
                            slug={"en": "commercial-vehicles", "de": "nutzfahrzeuge", "tr": "ticari-araclar"},
                            icon="truck",
                            is_enabled=True,
                            is_visible_on_home=True,
                            path=f"{vehicle_root.path}.NEW", # Will update ID after flush
                            depth=1,
                            allowed_countries=["DE", "TR", "FR"]
                        )
                        session.add(comm_veh_cat)
                        await session.flush()
                        comm_veh_cat.path = f"{vehicle_root.path}.{comm_veh_cat.id}"
                        session.add(CategoryTranslation(category_id=comm_veh_cat.id, language="en", name="Commercial Vehicles"))
                        session.add(CategoryTranslation(category_id=comm_veh_cat.id, language="tr", name="Ticari Araçlar"))
                        session.add(CategoryTranslation(category_id=comm_veh_cat.id, language="de", name="Nutzfahrzeuge"))
                        all_cats.append(comm_veh_cat)

                async def link(cat_slug, attr_keys):
                    target_cat = next((c for c in all_cats if c.slug.get('en') == cat_slug), None)
                    if not target_cat:
                        # Fallback for roots
                        if cat_slug == "vehicles": 
                             target_cat = vehicle_root
                    
                    if not target_cat:
                        logger.warning(f"⚠️ Category not found: {cat_slug}")
                        return

                    await session.execute(delete(CategoryAttributeMap).where(CategoryAttributeMap.category_id == target_cat.id))
                    
                    for key in attr_keys:
                        if key in attr_map:
                            session.add(CategoryAttributeMap(
                                category_id=target_cat.id,
                                attribute_id=attr_map[key],
                                inherit_to_children=True
                            ))
                    logger.info(f"🔗 Linked attributes to {cat_slug}")

                global_keys = [x[0] for x in global_attrs]
                car_keys = [x[0] for x in car_attrs]
                moto_keys = [x[0] for x in moto_attrs]
                comm_keys = [x[0] for x in comm_attrs]

                await link("vehicles", global_keys)
                await link("cars", car_keys)
                await link("motorcycles", moto_keys)
                await link("commercial-vehicles", comm_keys)

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
