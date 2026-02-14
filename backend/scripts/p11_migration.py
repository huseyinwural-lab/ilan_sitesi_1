
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import engine
from app.models.base import Base
# Import new models to ensure they are in metadata
from app.models.billing import BillingCustomer, StripeSubscription

async def upgrade_db():
    print("🚀 Starting P11 Billing Migration...")
    async with engine.begin() as conn:
        print("Creating tables...")
        # create_all checks for existence, so safe to run
        await conn.run_sync(Base.metadata.create_all)
        
        # Manually verify or add constraints if needed
        
    print("✅ Tables Created/Verified.")

if __name__ == "__main__":
    asyncio.run(upgrade_db())
