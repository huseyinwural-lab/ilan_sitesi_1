
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
from app.models.category import Category
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_v3")

async def seed_v3(allow_prod=False, dry_run=False):
    is_prod = os.environ.get("APP_ENV") == "production"
    
    if is_prod and not allow_prod:
        logger.error("🚫 STOP: Production requires --allow-prod flag and explicit intent.")
        return

    logger.info(f"🚀 Starting Seed v3 (EU Standard Attributes) - Dry Run: {dry_run}")

    async with AsyncSessionLocal() as session:
        try:
            # === DEFINITIONS ===
            
            # 1. GLOBAL ATTRIBUTES (Unchanged)
            global_attrs = [
                ("m2_gross", "number", "m²", {"en": "Gross Area", "tr": "Brüt m²", "de": "Bruttofläche", "fr": "Surface Brute"}),
                ("m2_net", "number", "m²", {"en": "Net Area", "tr": "Net m²", "de": "Nettofläche", "fr": "Surface Nette"}),
                ("building_status", "select", None, {"en": "Building Status", "tr": "Yapı Durumu", "de": "Zustand", "fr": "État"}),
                ("heating_type", "select", None, {"en": "Heating", "tr": "Isıtma", "de": "Heizung", "fr": "Chauffage"}),
                ("eligible_for_bank", "boolean", None, {"en": "Bank Loan Eligible", "tr": "Krediye Uygun", "de": "Kreditmöglich", "fr": "Éligible Crédit"}),
                ("swap_available", "boolean", None, {"en": "Swap Available", "tr": "Takaslı", "de": "Tausch möglich", "fr": "Échange possible"}),
                ("dues", "number", "EUR", {"en": "Dues", "tr": "Aidat", "de": "Hausgeld", "fr": "Charges"}),
            ]

            # 2. RESIDENTIAL ATTRIBUTES (Updated)
            res_attrs = [
                ("room_count", "select", None, {"en": "Rooms", "tr": "Oda Sayısı", "de": "Zimmer", "fr": "Pièces"}), # EU Standard
                ("has_kitchen", "boolean", None, {"en": "Kitchen", "tr": "Mutfak", "de": "Einbauküche", "fr": "Cuisine"}), # New Boolean
                ("floor_location", "select", None, {"en": "Floor", "tr": "Bulunduğu Kat", "de": "Etage", "fr": "Étage"}),
                ("bathroom_count", "select", None, {"en": "Bathrooms", "tr": "Banyo Sayısı", "de": "Badezimmer", "fr": "Salles de bain"}),
                ("balcony", "boolean", None, {"en": "Balcony", "tr": "Balkon", "de": "Balkon", "fr": "Balcon"}),
                ("furnished", "boolean", None, {"en": "Furnished", "tr": "Eşyalı", "de": "Möbliert", "fr": "Meublé"}),
                ("in_complex", "boolean", None, {"en": "In Complex", "tr": "Site İçerisinde", "de": "In Wohnanlage", "fr": "Dans résidence"}),
            ]

            # 3. COMMERCIAL ATTRIBUTES (Unchanged)
            comm_attrs = [
                ("ceiling_height", "number", "m", {"en": "Ceiling Height", "tr": "Tavan Yüksekliği", "de": "Deckenhöhe", "fr": "Hauteur plafond"}),
                ("entrance_height", "number", "m", {"en": "Entrance Height", "tr": "Giriş Yüksekliği", "de": "Einfahrtshöhe", "fr": "Hauteur entrée"}),
                ("power_capacity", "number", "kW", {"en": "Power Capacity", "tr": "Elektrik Gücü", "de": "Stromkapazität", "fr": "Puissance électrique"}),
                ("crane", "boolean", None, {"en": "Crane", "tr": "Vinç", "de": "Kran", "fr": "Grue"}),
                ("is_transfer", "boolean", None, {"en": "Transfer", "tr": "Devren", "de": "Ablöse", "fr": "Cession"}),
                ("ground_survey", "select", None, {"en": "Ground Survey", "tr": "Zemin Etüdü", "de": "Bodengutachten", "fr": "Étude de sol"}),
            ]

            # 4. OPTIONS (Updated)
            options_map = {
                "room_count": [
                    ("1", {"en": "1 Room", "tr": "1 Oda", "de": "1 Zimmer", "fr": "1 Pièce"}),
                    ("1.5", {"en": "1.5 Rooms", "tr": "1.5 Oda", "de": "1.5 Zimmer", "fr": "1.5 Pièces"}),
                    ("2", {"en": "2 Rooms", "tr": "2 Oda", "de": "2 Zimmer", "fr": "2 Pièces"}),
                    ("2.5", {"en": "2.5 Rooms", "tr": "2.5 Oda", "de": "2.5 Zimmer", "fr": "2.5 Pièces"}),
                    ("3", {"en": "3 Rooms", "tr": "3 Oda", "de": "3 Zimmer", "fr": "3 Pièces"}),
                    ("3.5", {"en": "3.5 Rooms", "tr": "3.5 Oda", "de": "3.5 Zimmer", "fr": "3.5 Pièces"}),
                    ("4", {"en": "4 Rooms", "tr": "4 Oda", "de": "4 Zimmer", "fr": "4 Pièces"}),
                    ("4.5", {"en": "4.5 Rooms", "tr": "4.5 Oda", "de": "4.5 Zimmer", "fr": "4.5 Pièces"}),
                    ("5", {"en": "5 Rooms", "tr": "5 Oda", "de": "5 Zimmer", "fr": "5 Pièces"}),
                    ("6", {"en": "6 Rooms", "tr": "6 Oda", "de": "6 Zimmer", "fr": "6 Pièces"}),
                    ("7+", {"en": "7+ Rooms", "tr": "7+ Oda", "de": "7+ Zimmer", "fr": "7+ Pièces"}),
                ],
                "building_status": [
                    ("new", {"en": "New", "tr": "Sıfır", "de": "Neubau", "fr": "Neuf"}),
                    ("used", {"en": "Used", "tr": "İkinci El", "de": "Altbau", "fr": "Ancien"}),
                    ("construction", {"en": "Under Construction", "tr": "Yapım Aşamasında", "de": "Im Bau", "fr": "En construction"}),
                ],
                "heating_type": [
                    ("combi_gas", {"en": "Combi (Gas)", "tr": "Kombi (Doğalgaz)", "de": "Gas-Etagenheizung", "fr": "Chauffage au gaz"}),
                    ("central", {"en": "Central", "tr": "Merkezi", "de": "Zentralheizung", "fr": "Chauffage central"}),
                    ("electric", {"en": "Electric", "tr": "Elektrikli", "de": "Elektroheizung", "fr": "Électrique"}),
                    ("floor", {"en": "Underfloor", "tr": "Yerden Isıtma", "de": "Fußbodenheizung", "fr": "Chauffage au sol"}),
                    ("none", {"en": "None", "tr": "Yok", "de": "Keine", "fr": "Aucune"}),
                ],
                "floor_location": [
                    ("basement", {"en": "Basement", "tr": "Bodrum", "de": "Keller", "fr": "Sous-sol"}),
                    ("ground", {"en": "Ground", "tr": "Giriş", "de": "Erdgeschoss", "fr": "Rez-de-chaussée"}),
                    ("1", {"en": "1", "tr": "1", "de": "1", "fr": "1"}),
                    ("2", {"en": "2", "tr": "2", "de": "2", "fr": "2"}),
                    ("3", {"en": "3", "tr": "3", "de": "3", "fr": "3"}),
                    ("top", {"en": "Top Floor", "tr": "En Üst", "de": "Dachgeschoss", "fr": "Dernier étage"}),
                ],
                "bathroom_count": [
                    ("1", {"en": "1", "tr": "1", "de": "1", "fr": "1"}),
                    ("2", {"en": "2", "tr": "2", "de": "2", "fr": "2"}),
                    ("3+", {"en": "3+", "tr": "3+", "de": "3+", "fr": "3+"}),
                ],
                "ground_survey": [
                    ("done", {"en": "Done", "tr": "Yapıldı", "de": "Ja", "fr": "Oui"}),
                    ("not_done", {"en": "Not Done", "tr": "Yapılmadı", "de": "Nein", "fr": "Non"}),
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

            # Process All Attributes
            all_definitions = global_attrs + res_attrs + comm_attrs
            attr_map = {}

            for key, type_name, unit, name in all_definitions:
                attr = await upsert_attr(key, type_name, unit, name)
                if not dry_run:
                    attr_map[key] = attr.id
                    
                    # Options
                    if key in options_map:
                        # Clear old options
                        await session.execute(delete(AttributeOption).where(AttributeOption.attribute_id == attr.id))
                        for idx, (val, label) in enumerate(options_map[key]):
                            opt = AttributeOption(
                                attribute_id=attr.id,
                                value=val,
                                label=label,
                                sort_order=idx
                            )
                            session.add(opt)

            # === BINDING ===
            if not dry_run:
                logger.info("Linking Attributes to Categories...")
                res = await session.execute(select(Category))
                all_cats = res.scalars().all()
                
                async def link(cat_slug, attr_keys):
                    target_cat = None
                    for c in all_cats:
                        slug_val = c.slug.get('en') if isinstance(c.slug, dict) else c.slug
                        if slug_val == cat_slug or \
                           slug_val == cat_slug.replace("-", "_") or \
                           slug_val == cat_slug.replace("_", "-"):
                            target_cat = c
                            break
                    
                    if not target_cat:
                        if cat_slug == "real-estate": # Fallback root
                             for c in all_cats:
                                 if c.module == "real_estate" and c.parent_id is None:
                                     target_cat = c
                                     break
                    
                    if not target_cat:
                        logger.warning(f"⚠️ Category not found: {cat_slug}")
                        return

                    # Delete old mappings
                    await session.execute(delete(CategoryAttributeMap).where(CategoryAttributeMap.category_id == target_cat.id))
                    
                    count = 0
                    for key in attr_keys:
                        if key in attr_map:
                            mapping = CategoryAttributeMap(
                                category_id=target_cat.id,
                                attribute_id=attr_map[key],
                                inherit_to_children=True
                            )
                            session.add(mapping)
                            count += 1
                    logger.info(f"🔗 Linked {count} attributes to {target_cat.slug.get('en')}")
                
                # Links
                global_keys = [x[0] for x in global_attrs]
                res_keys = [x[0] for x in res_attrs]
                comm_keys = [x[0] for x in comm_attrs]

                await link("real-estate", global_keys) 
                await link("housing", res_keys)       
                await link("commercial", comm_keys)   

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
    
    asyncio.run(seed_v3(allow_prod=args.allow_prod, dry_run=args.dry_run))
