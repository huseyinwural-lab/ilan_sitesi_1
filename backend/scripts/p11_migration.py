
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import engine
from app.models.base import Base
from app.models.billing import BillingCustomer, StripeSubscription, StripeEvent

async def upgrade_db():
    print("🚀 Starting P11 Billing Migration...")
    async with engine.begin() as conn:
        print("Creating tables...")
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables Created.")

if __name__ == "__main__":
    asyncio.run(upgrade_db())
