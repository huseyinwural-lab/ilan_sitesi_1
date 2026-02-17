
import asyncio
import os
import sys
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from scripts.seed_new_country import seed_new_country

async def test_seed_automation():
    # Test launching Italy (IT)
    await seed_new_country("IT", "Italy", "EUR", "it")

if __name__ == "__main__":
    asyncio.run(test_seed_automation())
