
import asyncio
import logging
import sys
import os
import argparse
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_shopping_md")

async def seed_shopping_master_data(allow_prod=False, dry_run=False):
    is_prod = os.environ.get("APP_ENV") == "production"
    if is_prod and not allow_prod:
        logger.error("🚫 STOP: Production requires --allow-prod.")
        return

    logger.info(f"🛍️ Starting Shopping Master Data Seed (v6)...")

    async with AsyncSessionLocal() as session:
        try:
            # === 1. ATTRIBUTES ===
            attrs = [
                # Global
                ("condition_shopping", "select", None, {"en": "Condition", "tr": "Durum", "de": "Zustand"}, False),
                ("shipping_available", "boolean", None, {"en": "Shipping Available", "tr": "Kargo Var", "de": "Versand möglich"}, False),
                
                # Electronics
                ("brand_electronics", "select", None, {"en": "Brand", "tr": "Marka", "de": "Marke"}, False),
                ("storage_capacity", "select", None, {"en": "Storage", "tr": "Hafıza", "de": "Speicher"}, False),
                ("ram", "select", None, {"en": "RAM", "tr": "RAM", "de": "RAM"}, False),
                ("screen_size", "number", "inch", {"en": "Screen Size", "tr": "Ekran Boyutu", "de": "Bildschirmgröße"}, False),
                ("warranty", "boolean", None, {"en": "Warranty", "tr": "Garanti", "de": "Garantie"}, False),

                # Fashion (Variants)
                ("size_apparel", "select", None, {"en": "Size", "tr": "Beden", "de": "Größe"}, True),
                ("size_shoes", "select", None, {"en": "Shoe Size", "tr": "Ayakkabı Numarası", "de": "Schuhgröße"}, True),
                ("color", "select", None, {"en": "Color", "tr": "Renk", "de": "Farbe"}, True),
                ("gender", "select", None, {"en": "Gender", "tr": "Cinsiyet", "de": "Geschlecht"}, False),
                ("brand_fashion", "text", None, {"en": "Brand", "tr": "Marka", "de": "Marke"}, False), # Text for fashion

                # Home
                ("material", "select", None, {"en": "Material", "tr": "Malzeme", "de": "Material"}, False),
            ]

            attr_map = {}
            for key, type_name, unit, name, is_variant in attrs:
                res = await session.execute(select(Attribute).where(Attribute.key == key))
                attr = res.scalar_one_or_none()
                if not attr:
                    attr = Attribute(key=key, attribute_type=type_name, unit=unit, name=name, is_variant=is_variant, is_active=True, is_filterable=True)
                    session.add(attr)
                # Ensure is_variant is updated if exists
                attr.is_variant = is_variant
                attr_map[key] = attr
            
            if not dry_run:
                await session.flush()

            # === 2. OPTIONS ===
            options = {
                "condition_shopping": [("new", {"en": "New"}), ("used", {"en": "Used"}), ("refurbished", {"en": "Refurbished"})],
                "brand_electronics": [("apple", {"en": "Apple"}), ("samsung", {"en": "Samsung"}), ("sony", {"en": "Sony"}), ("lg", {"en": "LG"}), ("xiaomi", {"en": "Xiaomi"})],
                "storage_capacity": [("64gb", {"en": "64 GB"}), ("128gb", {"en": "128 GB"}), ("256gb", {"en": "256 GB"}), ("512gb", {"en": "512 GB"}), ("1tb", {"en": "1 TB"})],
                "ram": [("4gb", {"en": "4 GB"}), ("8gb", {"en": "8 GB"}), ("16gb", {"en": "16 GB"}), ("32gb", {"en": "32 GB"})],
                "size_apparel": [("xs", {"en": "XS"}), ("s", {"en": "S"}), ("m", {"en": "M"}), ("l", {"en": "L"}), ("xl", {"en": "XL"})],
                "size_shoes": [("38", {"en": "38"}), ("39", {"en": "39"}), ("40", {"en": "40"}), ("41", {"en": "41"}), ("42", {"en": "42"}), ("43", {"en": "43"})],
                "color": [("black", {"en": "Black"}), ("white", {"en": "White"}), ("red", {"en": "Red"}), ("blue", {"en": "Blue"})],
                "gender": [("men", {"en": "Men"}), ("women", {"en": "Women"}), ("unisex", {"en": "Unisex"}), ("kids", {"en": "Kids"})],
                "material": [("wood", {"en": "Wood"}), ("metal", {"en": "Metal"}), ("glass", {"en": "Glass"}), ("fabric", {"en": "Fabric"})],
            }

            for key, opts in options.items():
                if key in attr_map:
                    attr_id = attr_map[key].id
                    # Clear old (Simplification)
                    await session.execute(delete(AttributeOption).where(AttributeOption.attribute_id == attr_id))
                    for i, (val, label) in enumerate(opts):
                        session.add(AttributeOption(attribute_id=attr_id, value=val, label=label, sort_order=i))

            # === 3. CATEGORIES & BINDING ===
            # Create Shopping Root
            root_res = await session.execute(select(Category).where(Category.module == 'shopping', Category.parent_id == None))
            root = root_res.scalar_one_or_none()
            if not root:
                root = Category(module="shopping", slug={"en": "shopping", "tr": "alisveris", "de": "einkaufen"}, is_enabled=True, allowed_countries=["DE","TR","FR"])
                session.add(root)
                await session.flush()
                root.path = str(root.id)

            # Define Subcats (Ensure they exist)
            subcats = [
                ("electronics", "Electronics", root),
                ("fashion", "Fashion", root),
                ("home-living", "Home & Living", root),
                ("hobbies", "Hobbies", root)
            ]
            
            # Level 2
            # Electronics -> Smartphones, Computers
            # Fashion -> Clothing, Shoes
            # Home -> Furniture
            
            # Helper to get/create cat
            async def get_create_cat(slug, name, parent):
                res = await session.execute(select(Category).where(Category.slug['en'].astext == slug)) # JSONB query might differ per driver
                # Simple python filter for seed reliability
                all_c = (await session.execute(select(Category).where(Category.module == 'shopping'))).scalars().all()
                cat = next((c for c in all_c if c.slug.get('en') == slug), None)
                
                if not cat:
                    logger.info(f"🆕 Creating Category: {slug}")
                    cat = Category(
                        module="shopping",
                        parent_id=parent.id,
                        slug={"en": slug}, # Simplified
                        is_enabled=True,
                        path=f"{parent.path}.NEW"
                    )
                    session.add(cat)
                    await session.flush()
                    cat.path = f"{parent.path}.{cat.id}"
                    session.add(CategoryTranslation(category_id=cat.id, language="en", name=name))
                return cat

            # L1
            cat_elec = await get_create_cat("electronics", "Electronics", root)
            cat_fash = await get_create_cat("fashion", "Fashion", root)
            cat_home = await get_create_cat("home-living", "Home & Living", root)
            
            # L2
            cat_phones = await get_create_cat("smartphones", "Smartphones", cat_elec)
            cat_comps = await get_create_cat("computers", "Computers", cat_elec)
            cat_cloth = await get_create_cat("clothing", "Clothing", cat_fash)
            cat_shoes = await get_create_cat("shoes", "Shoes", cat_fash)
            cat_furn = await get_create_cat("furniture", "Furniture", cat_home)

            async def link(target_cat, attr_keys):
                if not target_cat: return
                await session.execute(delete(CategoryAttributeMap).where(CategoryAttributeMap.category_id == target_cat.id))
                for key in attr_keys:
                    session.add(CategoryAttributeMap(category_id=target_cat.id, attribute_id=attr_map[key].id, inherit_to_children=True))
                logger.info(f"🔗 Linked to {target_cat.slug.get('en')}")

            # Bindings
            await link(root, ["condition_shopping", "shipping_available"])
            await link(cat_elec, ["brand_electronics", "warranty"])
            await link(cat_phones, ["storage_capacity", "ram", "screen_size"])
            await link(cat_comps, ["storage_capacity", "ram", "screen_size"])
            
            await link(cat_fash, ["gender", "brand_fashion", "color"])
            await link(cat_cloth, ["size_apparel"])
            await link(cat_shoes, ["size_shoes"])
            
            await link(cat_furn, ["material"])
            
            if not dry_run:
                await session.commit()
                logger.info("✅ Shopping Master Data Seeded.")

        except Exception as e:
            logger.error(f"❌ Error: {e}")
            await session.rollback()
            raise e

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-prod", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed_shopping_master_data(args.allow_prod, args.dry_run))
