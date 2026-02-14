
import asyncio
import httpx
import os

API_URL = "http://127.0.0.1:8001/api/v1/billing/checkout"

async def test_checkout():
    async with httpx.AsyncClient() as client:
        res = await client.post(API_URL, json={"plan_code": "TR_DEALER_PRO"})
        print(f"Status: {res.status_code}")

if __name__ == "__main__":
    asyncio.run(test_checkout())
