
import asyncio
import sys
import os
from sqlalchemy import text
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from scripts.process_expirations import process_expirations

async def force_expire_and_run():
    async with AsyncSessionLocal() as session:
        # Force set expires_at to past for 'Test Renew' listing
        await session.execute(text("UPDATE listings SET expires_at = NOW() - INTERVAL '1 day', status = 'active' WHERE title = 'Test Renew'"))
        await session.commit()
        print("forced expired")

    await process_expirations()

if __name__ == "__main__":
    asyncio.run(force_expire_and_run())
