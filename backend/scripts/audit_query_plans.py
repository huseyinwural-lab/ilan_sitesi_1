
import asyncio
import sys
import os
import json
import uuid
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category
from app.models.attribute import Attribute, AttributeOption

async def analyze_queries():
    print("🔍 Starting Query Plan Audit (EXPLAIN ANALYZE)...")
    
    async with AsyncSessionLocal() as session:
        # 1. Fetch Context (Category & Attributes for constructing queries)
        res = await session.execute(text("SELECT id, slug FROM categories WHERE slug->>'en' = 'smartphones' LIMIT 1"))
        cat = res.fetchone()
        if not cat:
            print("❌ 'smartphones' category not found. Cannot audit.")
            return
        
        cat_id = cat.id
        
        # Find Attributes
        res_attr = await session.execute(text("SELECT id, key FROM attributes WHERE key = 'brand_electronics' LIMIT 1"))
        brand_attr = res_attr.fetchone()
        
        res_opt = await session.execute(text(f"SELECT id FROM attribute_options WHERE attribute_id = '{brand_attr.id}' LIMIT 1"))
        brand_opt = res_opt.fetchone()
        
        if not brand_attr or not brand_opt:
            print("❌ Attributes not found.")
            return

        print(f"Context: Category={cat_id}, BrandAttr={brand_attr.id}, Option={brand_opt.id}")

        # === Q1: Base Paging ===
        print("\n--- Q1: Base Category Paging ---")
        q1 = f"""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT * FROM listings 
        WHERE category_id = '{cat_id}' AND status = 'active'
        ORDER BY created_at DESC, id DESC 
        LIMIT 20
        """
        await run_explain(session, q1)

        # === Q2: 1 Select Filter (Brand) ===
        print("\n--- Q2: Filter by Brand ---")
        q2 = f"""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT l.id FROM listings l
        WHERE l.category_id = '{cat_id}' AND l.status = 'active'
        AND EXISTS (
            SELECT 1 FROM listing_attributes la 
            WHERE la.listing_id = l.id 
            AND la.attribute_id = '{brand_attr.id}' 
            AND la.value_option_id = '{brand_opt.id}'
        )
        LIMIT 20
        """
        await run_explain(session, q2)

        # === Q3: Facet Aggregation (Brand) ===
        # Note: This aggregates over the WHOLE filtered set (no limit)
        print("\n--- Q3: Facet Aggregation ---")
        q3 = f"""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT ao.value, count(*)
        FROM listing_attributes la
        JOIN attribute_options ao ON la.value_option_id = ao.id
        WHERE la.attribute_id = '{brand_attr.id}'
        AND la.listing_id IN (
            SELECT id FROM listings 
            WHERE category_id = '{cat_id}' AND status = 'active'
        )
        GROUP BY ao.value
        """
        await run_explain(session, q3)

async def run_explain(session, query):
    try:
        res = await session.execute(text(query))
        rows = res.fetchall()
        for row in rows:
            print(row[0])
    except Exception as e:
        print(f"❌ Query Failed: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_queries())
