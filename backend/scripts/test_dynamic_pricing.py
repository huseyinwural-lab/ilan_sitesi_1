
import asyncio
import os
import sys
import uuid
import httpx
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import text, select

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.services.price_service import PriceService
from app.models.premium import PremiumProduct

async def test_dynamic_pricing():
    print("🚀 Starting Dynamic Pricing Test...")
    
    # 1. Setup Premium Product
    async with AsyncSessionLocal() as session:
        # Ensure base product exists
        await session.execute(text("DELETE FROM premium_products WHERE key = 'TEST_DYN_SHOWCASE'"))
        prod_id = uuid.uuid4()
        await session.execute(text(f"INSERT INTO premium_products (id, key, name, country, currency, price_net, duration_days, is_active, tax_category, created_at, updated_at, sort_order) VALUES ('{prod_id}', 'TEST_DYN_SHOWCASE', '{{\"en\": \"Test\"}}', 'TR', 'TRY', 100.00, 7, true, 'ads', NOW(), NOW(), 0)"))
        await session.commit()
        
        # Fetch object
        res = await session.execute(select(PremiumProduct).where(PremiumProduct.key == 'TEST_DYN_SHOWCASE'))
        product = res.scalar_one()
        
        service = PriceService(session)
        
        # 2. Test Cases
        
        # Case A: Base (Real Estate, Other City) -> x1.0 * x1.0 = 100.00
        ctx_a = {"category": "real_estate", "city": "izmit"}
        price_a = await service.calculate_premium_price(product, ctx_a)
        print(f"Case A (Base): {price_a} (Expected: ~100-110)")
        
        # Case B: High Value (Istanbul) -> x1.5 = 150.00
        ctx_b = {"category": "real_estate", "city": "istanbul"}
        price_b = await service.calculate_premium_price(product, ctx_b)
        print(f"Case B (Istanbul): {price_b} (Expected: ~150-165)")
        
        # Case C: Low Value Category (Shopping) -> x0.2 = 20.00
        ctx_c = {"category": "shopping", "city": "izmit"}
        price_c = await service.calculate_premium_price(product, ctx_c)
        print(f"Case C (Shopping): {price_c} (Expected: ~20-22)")
        
        # Check Multipliers
        if price_b > price_a and price_c < price_a:
            print("✅ Dynamic Logic Verified")
        else:
            print("❌ Logic Fail")

if __name__ == "__main__":
    asyncio.run(test_dynamic_pricing())
