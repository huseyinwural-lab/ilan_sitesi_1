
import asyncio
import sys
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.database import AsyncSessionLocal
from app.models.category import Category

async def inspect_cats():
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(Category))
        cats = res.scalars().all()
        print(f"Total Categories: {len(cats)}")
        for c in cats:
            print(f"ID: {c.id} | Module: {c.module} | Slug: {c.slug}")

if __name__ == "__main__":
    asyncio.run(inspect_cats())
