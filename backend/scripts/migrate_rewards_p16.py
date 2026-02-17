
import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

async def migrate_existing_rewards():
    print("🚀 Migrating Existing Rewards to 'confirmed' status...")
    async with AsyncSessionLocal() as session:
        # P16: Assume all existing 'applied' rewards are now 'confirmed'
        await session.execute(text("UPDATE referral_rewards SET status = 'confirmed' WHERE status = 'applied'"))
        
        # Pending remains pending.
        # We don't backfill ledger for old rewards to avoid balance double counting (since they were already applied to Stripe).
        # But for consistency, we might want to?
        # Decision: "applied" meant "credit given". "confirmed" means "credit given".
        # So we just rename status.
        
        await session.commit()
        print("✅ Migration Complete.")

if __name__ == "__main__":
    asyncio.run(migrate_existing_rewards())
