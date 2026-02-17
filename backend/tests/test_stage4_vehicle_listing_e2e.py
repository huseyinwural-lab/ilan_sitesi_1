import os
import json
import pytest
from fastapi.testclient import TestClient

from server import app


def _get_token(client: TestClient):
    resp = client.post(
        "/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


def _auth_headers(token: str):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("make_key,expect_status", [("bmw", 200), ("not-a-make", 200)])
def test_vehicle_draft_create(client_fixture, make_key, expect_status):
    client = client_fixture
    token = _get_token(client)

    payload = {
        "country": "DE",
        "category_key": "otomobil",
        "make_key": make_key,
        "model_key": "3-serie",
        "year": 2020,
        "mileage_km": 85000,
        "price_eur": 15000,
        "fuel_type": "electric",
        "transmission": "automatic",
        "condition": "used",
    }

    resp = client.post("/api/v1/listings/vehicle", json=payload, headers=_auth_headers(token))
    assert resp.status_code == expect_status
    assert resp.json()["status"] == "draft"


@pytest.fixture
def client_fixture():
    # Ensure env var points to seed directory; tests assume local FS exists
    os.environ.setdefault("VEHICLE_MASTER_DATA_DIR", "/data/vehicle_master")
    return TestClient(app)
