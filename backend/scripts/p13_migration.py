
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import engine

async def upgrade_db():
    print("🚀 Starting P13 Lifecycle Migration...")
    
    # We use raw connection for ALTER TABLE to avoid transaction blocks if using asyncpg in certain modes, 
    # though standard execute usually works. AUTOCOMMIT is safest for DDL.
    async with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        print("Adding columns...")
        
        # expires_at
        try:
            await conn.execute(text("ALTER TABLE listings ADD COLUMN expires_at TIMESTAMPTZ DEFAULT NULL"))
            print("✅ Added expires_at")
        except Exception as e:
            print(f"ℹ️  expires_at exists or error: {e}")

        # last_activity_at
        try:
            await conn.execute(text("ALTER TABLE listings ADD COLUMN last_activity_at TIMESTAMPTZ DEFAULT NOW()"))
            print("✅ Added last_activity_at")
        except Exception as e:
            print(f"ℹ️  last_activity_at exists or error: {e}")
            
        # Index for Expiration Job
        try:
            await conn.execute(text("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_listings_expires_at ON listings (expires_at) WHERE status = 'active'"))
            print("✅ Added index ix_listings_expires_at")
        except Exception as e:
            print(f"⚠️  Index error: {e}")

    print("Migration Complete.")

if __name__ == "__main__":
    asyncio.run(upgrade_db())
