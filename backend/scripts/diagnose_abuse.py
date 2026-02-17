
import asyncio
import httpx
from sqlalchemy import text
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal

async def diagnose_abuse():
    print("🚀 Diagnosing...")
    device_hash = "unique_device_fix"
    
    async with AsyncSessionLocal() as session:
        # Check current count in DB
        res = await session.execute(text(f"SELECT count(*) FROM users WHERE device_hash = '{device_hash}'"))
        count = res.scalar()
        print(f"Current DB Count for {device_hash}: {count}")
        
        # Check users
        res = await session.execute(text(f"SELECT email FROM users WHERE device_hash = '{device_hash}'"))
        users = res.fetchall()
        print(f"Users: {users}")

if __name__ == "__main__":
    asyncio.run(diagnose_abuse())
