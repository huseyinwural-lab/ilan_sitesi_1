import asyncio
import sys
import os
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap
from app.models.category import Category

# Path setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append("/app/backend")

async def seed_attributes():
    print("🛠️ Seeding Real Estate Attributes...")
    
    async with AsyncSessionLocal() as db:
        # 1. Define Attributes
        # Format: (Key, Type, {Name TR, EN, DE}, Required, Unit, Options)
        
        attributes_data = [
            ("m2_gross", "number", {"tr": "m² (Brüt)", "en": "Gross Area", "de": "Bruttofläche"}, True, "m²", None),
            ("m2_net", "number", {"tr": "m² (Net)", "en": "Net Area", "de": "Nettofläche"}, True, "m²", None),
            ("room_count", "select", {"tr": "Oda Sayısı", "en": "Rooms", "de": "Zimmer"}, True, None, [
                "1+0", "1+1", "2+1", "3+1", "3+2", "4+1", "4+2", "5+"
            ]),
            ("building_age", "select", {"tr": "Bina Yaşı", "en": "Building Age", "de": "Baujahr"}, True, None, [
                "0", "1", "2", "3", "4", "5-10", "11-15", "16-20", "21+"
            ]),
            ("floor_location", "select", {"tr": "Bulunduğu Kat", "en": "Floor", "de": "Etage"}, True, None, [
                "Giriş", "1", "2", "3", "4", "5", "6-10", "11-20", "20+"
            ]),
            ("heating_type", "select", {"tr": "Isıtma", "en": "Heating", "de": "Heizung"}, True, None, [
                "Yok", "Kombi (Doğalgaz)", "Merkezi", "Klima", "Yerden Isıtma"
            ]),
            ("balcony", "boolean", {"tr": "Balkon", "en": "Balcony", "de": "Balkon"}, False, None, None),
            ("furnished", "boolean", {"tr": "Eşyalı", "en": "Furnished", "de": "Möbliert"}, False, None, None),
            ("energy_class", "select", {"tr": "Enerji Sınıfı", "en": "Energy Class", "de": "Energieeffizienzklasse"}, False, None, [
                "A+++", "A++", "A+", "A", "B", "C", "D", "E", "F", "G"
            ]),
            ("vat_included", "boolean", {"tr": "KDV Dahil", "en": "VAT Included", "de": "MwSt. inklusive"}, False, None, None)
        ]
        
        created_attrs = {}
        
        for key, atype, names, req, unit, options in attributes_data:
            # Check existing
            res = await db.execute(select(Attribute).where(Attribute.key == key))
            attr = res.scalar_one_or_none()
            
            if not attr:
                attr = Attribute(
                    key=key,
                    name=names,
                    attribute_type=atype,
                    is_required=req,
                    is_filterable=True,
                    unit=unit
                )
                db.add(attr)
                await db.flush()
                
                # Add Options if select
                if options:
                    for i, opt_val in enumerate(options):
                        db.add(AttributeOption(
                            attribute_id=attr.id,
                            value=opt_val,
                            label={"tr": opt_val, "en": opt_val}, # Simplified translation
                            sort_order=i
                        ))
            
            created_attrs[key] = attr
            
        await db.commit()
        print("✅ Attributes Created.")
        
        # 2. Map to Categories
        # Strategy: Find "Konut" (Residential) root and map to all children?
        # Better: Map to specific sub-categories or Root based on inheritance logic.
        # Since inheritance is logic-based (U2.1), we can map to Root of Real Estate or L2 Segments.
        # Let's map to L2 segments for now.
        
        # Find L2 Segments
        # We need to find category IDs. Helper query.
        
        # Helper: Get all categories flat
        res = await db.execute(select(Category))
        all_cats = res.scalars().all()
        
        # Filter for Residential
        residential_cats = [c for c in all_cats if c.slug.get('en') == 'residential' or c.slug.get('tr') == 'residential']
        commercial_cats = [c for c in all_cats if c.slug.get('en') == 'commercial' or c.slug.get('tr') == 'commercial']
        
        # Mapping List
        # (Category List, Attribute Keys)
        mapping_plan = [
            (residential_cats, ["m2_gross", "m2_net", "room_count", "building_age", "floor_location", "heating_type", "balcony", "furnished", "energy_class"]),
            (commercial_cats, ["m2_gross", "m2_net", "heating_type", "building_age", "vat_included"])
        ]
        
        for cats, attr_keys in mapping_plan:
            for cat in cats:
                for a_key in attr_keys:
                    attr = created_attrs.get(a_key)
                    if attr:
                        # Check mapping
                        exists = await db.execute(select(CategoryAttributeMap).where(
                            CategoryAttributeMap.category_id == cat.id,
                            CategoryAttributeMap.attribute_id == attr.id
                        ))
                        if not exists.scalar_one_or_none():
                            db.add(CategoryAttributeMap(
                                category_id=cat.id,
                                attribute_id=attr.id,
                                inherit_to_children=True
                            ))
                            
        await db.commit()
        print("✅ Attributes Mapped.")

if __name__ == "__main__":
    asyncio.run(seed_attributes())
