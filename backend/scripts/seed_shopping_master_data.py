
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

            # Subcats
            def ensure_cat(slug, name, parent):
                cat = Category(module="shopping", parent_id=parent.id, slug={"en": slug}, is_enabled=True, path=f"{parent.path}.NEW")
                # Add logic to check existence first in real impl
                session.add(cat)
                return cat

            # Need robust Category Tree logic or reuse existing seed. 
            # Assuming Categories exist from Seed v1/v2 or we just link to existing ones.
            # Let's fetch existing subs.
            
            all_cats = (await session.execute(select(Category).where(Category.module == 'shopping'))).scalars().all()
            
            async def link(cat_slug, attr_keys):
                cat = next((c for c in all_cats if c.slug.get('en') == cat_slug), None)
                if not cat: 
                    # If not found, skip or create. For seed v6, we assume categories exist from previous seed or we skip.
                    logger.warning(f"⚠️ Category {cat_slug} not found. Skipping binding.")
                    return
                
                await session.execute(delete(CategoryAttributeMap).where(CategoryAttributeMap.category_id == cat.id))
                for key in attr_keys:
                    session.add(CategoryAttributeMap(category_id=cat.id, attribute_id=attr_map[key].id, inherit_to_children=True))
                logger.info(f"🔗 Linked to {cat_slug}")

            # Bindings
            await link("shopping", ["condition_shopping", "shipping_available"])
            await link("electronics", ["brand_electronics", "warranty"])
            await link("smartphones", ["storage_capacity", "ram", "screen_size"])
            await link("computers", ["storage_capacity", "ram", "screen_size"])
            
            # Fashion (Need to ensure 'fashion' cat exists, v1 seed had 'shopping' -> 'electronics', 'home'. Fashion might be missing)
            # If missing, script ends here for Fashion.
            
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
