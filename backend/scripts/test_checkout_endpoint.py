
import asyncio
import httpx
import os

API_URL = "http://127.0.0.1:8001/api/payments/create-checkout-session"

async def test_checkout():
    async with httpx.AsyncClient() as client:
        res = await client.post(API_URL, json={"invoice_id": "legacy-script-update-required", "origin_url": "http://127.0.0.1:3000"})
        print(f"Status: {res.status_code}")

if __name__ == "__main__":
    asyncio.run(test_checkout())
