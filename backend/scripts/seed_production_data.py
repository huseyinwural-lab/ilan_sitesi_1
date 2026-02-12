
import asyncio
import logging
import sys
import os
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("production_seed")

async def seed_production_data():
    logger.info("Starting Production Data Seed (DE Market)...")
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Clear Old Data (Safety: Only if explicitly intended for fresh start)
            logger.info("Clearing existing Category and Attribute data...")
            await session.execute(delete(CategoryAttributeMap))
            await session.execute(delete(CategoryTranslation))
            await session.execute(delete(Category))
            await session.execute(delete(AttributeOption))
            await session.execute(delete(Attribute))
            await session.commit()
            logger.info("Data cleared.")

            # 2. Create Attributes
            logger.info("Creating Attributes...")
            
            # Helper to create attribute
            async def create_attr(key, name_en, name_de, name_tr, type="text", unit=None, options=None):
                attr = Attribute(
                    key=key,
                    name={"en": name_en, "de": name_de, "tr": name_tr},
                    attribute_type=type, # text, number, select
                    unit=unit,
                    is_active=True,
                    is_filterable=True
                )
                session.add(attr)
                await session.flush() # Get ID
                
                if options:
                    for i, opt_val in enumerate(options):
                        opt = AttributeOption(
                            attribute_id=attr.id,
                            value=opt_val,
                            label={"en": opt_val, "de": opt_val, "tr": opt_val}, # Simplification
                            sort_order=i
                        )
                        session.add(opt)
                return attr

            # Define Attributes
            attrs = {}
            attrs['m2'] = await create_attr("m2", "Size", "Fläche", "m2", "number", "m²")
            attrs['room_count'] = await create_attr("room_count", "Rooms", "Zimmer", "Oda Sayısı", "select", None, ["1", "1.5", "2", "2.5", "3", "4", "5+"])
            attrs['floor'] = await create_attr("floor", "Floor", "Etage", "Kat", "number")
            attrs['heating'] = await create_attr("heating_type", "Heating", "Heizung", "Isıtma", "select", None, ["Gas", "Electric", "Central", "Heat Pump"])
            attrs['comm_type'] = await create_attr("commercial_type", "Type", "Typ", "Tip", "select", None, ["Office", "Shop", "Warehouse", "Hotel"])
            
            attrs['brand_car'] = await create_attr("brand_car", "Brand", "Marke", "Marka", "select", None, ["BMW", "Mercedes", "VW", "Audi", "Tesla", "Ford"])
            attrs['model'] = await create_attr("model", "Model", "Modell", "Model", "text")
            attrs['year'] = await create_attr("year", "Year", "Baujahr", "Yıl", "number")
            attrs['km'] = await create_attr("km", "Mileage", "Kilometerstand", "KM", "number", "km")
            attrs['fuel'] = await create_attr("fuel_type", "Fuel", "Kraftstoff", "Yakıt", "select", None, ["Petrol", "Diesel", "Hybrid", "Electric"])
            attrs['gear'] = await create_attr("gear_type", "Gearbox", "Getriebe", "Vites", "select", None, ["Manual", "Automatic"])
            
            attrs['brand_moto'] = await create_attr("brand_moto", "Brand", "Marke", "Marka", "select", None, ["Yamaha", "Honda", "Kawasaki", "Ducati"])
            attrs['cc'] = await create_attr("cc", "Cubic Capacity", "Hubraum", "Silindir Hacmi", "number", "cm³")
            
            attrs['brand_gen'] = await create_attr("brand_generic", "Brand", "Marke", "Marka", "text")
            attrs['storage'] = await create_attr("storage", "Storage", "Speicher", "Depolama", "select", None, ["64GB", "128GB", "256GB", "512GB", "1TB"])
            attrs['processor'] = await create_attr("processor", "Processor", "Prozessor", "İşlemci", "text")
            attrs['ram'] = await create_attr("ram", "RAM", "RAM", "RAM", "select", None, ["8GB", "16GB", "32GB"])

            await session.commit()
            logger.info("Attributes created.")

            # 3. Create Categories & Mapping
            logger.info("Creating Categories...")

            async def create_cat(module, slug_en, name_en, name_de, name_tr, icon, parent=None, linked_attrs=[]):
                cat = Category(
                    module=module,
                    parent_id=parent.id if parent else None,
                    slug={"en": slug_en, "de": slug_en, "tr": slug_en}, # Simplified slug logic
                    icon=icon,
                    is_enabled=True,
                    is_visible_on_home=True,
                    allowed_countries=["DE", "AT", "CH", "FR"] # Global for now
                )
                session.add(cat)
                await session.flush()
                
                # Add translations
                session.add(CategoryTranslation(category_id=cat.id, language="en", name=name_en))
                session.add(CategoryTranslation(category_id=cat.id, language="de", name=name_de))
                session.add(CategoryTranslation(category_id=cat.id, language="tr", name=name_tr))
                
                # Update path
                cat.path = f"{parent.path}.{cat.id}" if parent else str(cat.id)
                cat.depth = (parent.depth + 1) if parent else 0
                
                # Map Attributes
                for attr_key in linked_attrs:
                    if attr_key in attrs:
                        mapping = CategoryAttributeMap(
                            category_id=cat.id,
                            attribute_id=attrs[attr_key].id,
                            inherit_to_children=True
                        )
                        session.add(mapping)
                
                return cat

            # --- REAL ESTATE ---
            cat_re = await create_cat("real_estate", "real-estate", "Real Estate", "Immobilien", "Emlak", "building-2")
            
            # Housing
            cat_housing = await create_cat("real_estate", "housing", "Housing", "Wohnen", "Konut", "home", cat_re)
            # Subs
            await create_cat("real_estate", "apartment-sale", "Apartment for Sale", "Wohnung kaufen", "Satılık Daire", "key", cat_housing, ["m2", "room_count", "floor", "heating"])
            await create_cat("real_estate", "apartment-rent", "Apartment for Rent", "Mietwohnung", "Kiralık Daire", "key", cat_housing, ["m2", "room_count", "floor", "heating"])
            await create_cat("real_estate", "house-sale", "House for Sale", "Haus kaufen", "Satılık Ev", "home", cat_housing, ["m2", "room_count", "heating"])
            await create_cat("real_estate", "house-rent", "House for Rent", "Haus mieten", "Kiralık Ev", "home", cat_housing, ["m2", "room_count", "heating"])

            # Commercial
            cat_comm = await create_cat("real_estate", "commercial", "Commercial", "Gewerbe", "İşyeri", "briefcase", cat_re)
            await create_cat("real_estate", "office", "Office & Praxis", "Büro & Praxis", "Ofis", "monitor", cat_comm, ["m2", "comm_type"])
            await create_cat("real_estate", "retail", "Retail", "Einzelhandel", "Mağaza", "shopping-bag", cat_comm, ["m2", "comm_type"])

            # --- VEHICLES ---
            cat_veh = await create_cat("vehicle", "vehicles", "Vehicles", "Fahrzeuge", "Vasıta", "car")
            
            # Cars
            cat_cars = await create_cat("vehicle", "cars", "Cars", "Autos", "Otomobil", "car", cat_veh)
            await create_cat("vehicle", "used-cars", "Used Cars", "Gebrauchtwagen", "İkinci El", "car", cat_cars, ["brand_car", "model", "year", "km", "fuel", "gear"])
            await create_cat("vehicle", "new-cars", "New Cars", "Neuwagen", "Sıfır Araç", "star", cat_cars, ["brand_car", "model", "year", "fuel", "gear"])

            # Moto
            cat_moto = await create_cat("vehicle", "motorcycles", "Motorcycles", "Motorräder", "Motosiklet", "bike", cat_veh, ["brand_moto", "cc", "year", "km"])

            # --- SHOPPING ---
            cat_shop = await create_cat("shopping", "shopping", "Shopping", "Einkaufen", "Alışveriş", "shopping-cart")
            
            # Electronics
            cat_elec = await create_cat("shopping", "electronics", "Electronics", "Elektronik", "Elektronik", "smartphone", cat_shop)
            await create_cat("shopping", "smartphones", "Smartphones", "Handys", "Cep Telefonu", "smartphone", cat_elec, ["brand_gen", "storage"])
            await create_cat("shopping", "computers", "Computers", "Computer", "Bilgisayar", "monitor", cat_elec, ["brand_gen", "processor", "ram"])

            # Home
            cat_home = await create_cat("shopping", "home-garden", "Home & Garden", "Haus & Garten", "Ev & Bahçe", "sun", cat_shop)
            await create_cat("shopping", "furniture", "Furniture", "Möbel", "Mobilya", "armchair", cat_home)

            # --- SERVICES ---
            cat_serv = await create_cat("services", "services", "Services", "Dienstleistungen", "Hizmetler", "users")
            await create_cat("services", "tutoring", "Tutoring", "Nachhilfe", "Özel Ders", "book", cat_serv)
            await create_cat("services", "craftsmen", "Craftsmen", "Handwerker", "Ustalar", "hammer", cat_serv)

            await session.commit()
            logger.info("Category Tree Created Successfully.")

        except Exception as e:
            logger.error(f"Seeding Failed: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    asyncio.run(seed_production_data())
