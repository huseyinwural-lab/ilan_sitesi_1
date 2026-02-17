
import asyncio
import sys
import os
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

async def fix_sequence_and_clean():
    async with AsyncSessionLocal() as session:
        # 1. Clean existing abuse test users to reset count
        await session.execute(text("DELETE FROM users WHERE email LIKE 'abuse_fix_%@test.com'"))
        await session.commit()
        print("✅ Cleaned abuse test users.")

if __name__ == "__main__":
    asyncio.run(fix_sequence_and_clean())
