
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

async def manual_reset_abuse_fix():
    print("🚀 Manual Reset...")
    async with AsyncSessionLocal() as session:
        # Delete ANY user created by the abuse_fix script, regardless of sequence
        await session.execute(text("DELETE FROM users WHERE email LIKE 'abuse_fix_%'"))
        await session.commit()
    print("✅ Reset Done.")

if __name__ == "__main__":
    asyncio.run(manual_reset_abuse_fix())
