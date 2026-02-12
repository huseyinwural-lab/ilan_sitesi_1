
import pytest
import pytest_asyncio
import httpx
import os
import asyncio

# Use the internal service URL for testing within the container
BASE_URL = "http://localhost:8001/api"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def client():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as ac:
        yield ac

@pytest_asyncio.fixture(scope="session")
async def admin_token(client):
    # Login as admin
    response = await client.post("/auth/login", json={
        "email": "admin@platform.com",
        "password": os.environ.get('ADMIN_PASSWORD', 'Admin123!')
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]

@pytest_asyncio.fixture(scope="session")
async def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
