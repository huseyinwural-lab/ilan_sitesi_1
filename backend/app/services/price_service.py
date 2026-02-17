
import logging
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.pricing import PriceConfig
from app.models.premium import PremiumProduct
from datetime import datetime

logger = logging.getLogger(__name__)

class PriceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_premium_price(self, product: PremiumProduct, context: dict) -> Decimal:
        """
        Calculates dynamic price for a premium product.
        Context: {category: str, city: str, country: str}
        """
        base_price = product.price_net
        
        # 1. Category Multiplier
        category = context.get("category", "").lower()
        cat_mult = Decimal("1.0")
        if category == "real_estate":
            cat_mult = Decimal("1.0")
        elif category == "vehicle":
            cat_mult = Decimal("0.8")
        elif category == "shopping":
            cat_mult = Decimal("0.2")
        elif category == "services":
            cat_mult = Decimal("0.5")
            
        # 2. City Multiplier (Simplified Tier List)
        city = context.get("city", "").lower()
        city_mult = Decimal("1.0")
        tier1_cities = ["istanbul", "berlin", "paris", "london"]
        tier2_cities = ["ankara", "izmir", "munich", "lyon"]
        
        if city in tier1_cities:
            city_mult = Decimal("1.5")
        elif city in tier2_cities:
            city_mult = Decimal("1.2")
            
        # 3. Demand Multiplier (Weekend)
        # Check current time
        demand_mult = Decimal("1.0")
        now = datetime.now()
        if now.weekday() >= 5: # Sat, Sun
            demand_mult = Decimal("1.1")
            
        # Final Calculation
        final_price = base_price * cat_mult * city_mult * demand_mult
        
        # Rounding (2 decimals)
        return round(final_price, 2)

    async def get_pay_per_listing_price(self, country: str, category: str) -> Decimal:
        # Fetch base price from PriceConfig (P5)
        # Apply multipliers similarly
        # For P17 MVP, we focus on Premium Product dynamic pricing
        return Decimal("0.00") # Placeholder
