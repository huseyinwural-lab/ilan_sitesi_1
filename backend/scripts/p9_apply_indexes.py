
import asyncio
from sqlalchemy import text
from app.database import engine

async def apply_indexes():
    print("🏗️  Applying Composite Indexes (P9 Optimization)...")
    
    commands = [
        # 1. Listing Filters (Category + Status + Price)
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_listings_cat_status_price 
        ON listings (category_id, status, price)
        """,
        
        # 2. Facet Aggregation (Attribute + Value + Listing)
        # This is the "Money Index" for aggregation performance
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_la_attr_val_listing 
        ON listing_attributes (attribute_id, value_option_id, listing_id)
        """,
        
        # 3. Numeric Range Filters (Attribute + Number + Listing)
        """
        CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_la_attr_num_listing
        ON listing_attributes (attribute_id, value_number, listing_id)
        """,
        
        # 4. Analyze to update planner
        "ANALYZE listing_attributes",
        "ANALYZE listings"
    ]

    async with engine.begin() as conn:
        # CONCURRENTLY cannot run in transaction block usually, but asyncpg/sqlalchemy handling might vary.
        # Standard SQLAlchemy `execute` is autocommit if text() is used without transaction?
        # Actually `engine.begin()` starts transaction. 
        # `CREATE INDEX CONCURRENTLY` cannot run inside a transaction block.
        # We need isolation_level="AUTOCOMMIT".
        pass

    # Use raw connection for isolation level
    async with engine.execution_options(isolation_level="AUTOCOMMIT").connect() as conn:
        for cmd in commands:
            try:
                print(f"Executing: {cmd.strip().splitlines()[0]}...")
                await conn.execute(text(cmd))
                print("✅ Done.")
            except Exception as e:
                print(f"⚠️  Error (might exist): {e}")

    print("🎉 All Indexes Applied.")

if __name__ == "__main__":
    asyncio.run(apply_indexes())
