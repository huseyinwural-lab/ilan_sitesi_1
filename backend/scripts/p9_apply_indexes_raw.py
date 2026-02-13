
import asyncio
import asyncpg
import os

DB_DSN = os.environ.get("DATABASE_URL", "postgresql://admin_user:admin_pass@localhost:5432/admin_panel").replace('+asyncpg', '')

async def apply_indexes():
    print("🏗️  Applying Composite Indexes (Raw AsyncPG)...")
    
    commands = [
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_listings_cat_status_price ON listings (category_id, status, price)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_la_attr_val_listing ON listing_attributes (attribute_id, value_option_id, listing_id)",
        "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_la_attr_num_listing ON listing_attributes (attribute_id, value_number, listing_id)",
        "ANALYZE listing_attributes",
        "ANALYZE listings"
    ]

    conn = await asyncpg.connect(DB_DSN)
    try:
        for cmd in commands:
            print(f"Executing: {cmd}")
            await conn.execute(cmd)
            print("✅ Done.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_indexes())
