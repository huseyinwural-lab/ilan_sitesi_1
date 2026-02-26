"""
P63 Logo upload contract tests
- error_code contract (INVALID_FILE_TYPE / FILE_TOO_LARGE / INVALID_ASPECT_RATIO)
- scope/rbac behaviour
- storage health presence
"""
import os
import tempfile

import pytest
import requests
from PIL import Image


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def _login(email: str, password: str, portal: str):
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"X-Portal-Scope": portal},
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed for {email}: {response.status_code}")
    return response.json().get("access_token") or response.json().get("token")


def _image_bytes(width: int, height: int, fmt: str = "PNG") -> bytes:
    with tempfile.NamedTemporaryFile(suffix=f".{fmt.lower()}") as tmp:
        image = Image.new("RGB", (width, height), (240, 130, 20))
        image.save(tmp.name, format=fmt)
        with open(tmp.name, "rb") as handle:
            return handle.read()


def _detail(response):
    payload = response.json()
    detail = payload.get("detail")
    return detail if isinstance(detail, dict) else {"code": None, "message": str(detail or "")}


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")


@pytest.fixture(scope="module")
def dealer_token():
    return _login(DEALER_EMAIL, DEALER_PASSWORD, "dealer")


class TestLogoUploadContract:
    def test_invalid_file_type_contract(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("bad.txt", b"hello", "text/plain")},
            data={"segment": "corporate", "scope": "system"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        detail = _detail(response)
        assert detail.get("code") == "INVALID_FILE_TYPE"

    def test_file_too_large_contract(self, admin_token: str):
        large_bytes = os.urandom(2 * 1024 * 1024 + 1000)
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("large.png", large_bytes, "image/png")},
            data={"segment": "corporate", "scope": "system"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        detail = _detail(response)
        assert detail.get("code") == "FILE_TOO_LARGE"

    def test_invalid_aspect_ratio_contract(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("ratio.png", _image_bytes(250, 100, "PNG"), "image/png")},
            data={"segment": "corporate", "scope": "system"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 400
        detail = _detail(response)
        assert detail.get("code") == "INVALID_ASPECT_RATIO"

    def test_scope_system_with_scope_id_is_accepted(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("ok.png", _image_bytes(300, 100, "PNG"), "image/png")},
            data={"segment": "corporate", "scope": "system", "scope_id": "tenant-001"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        item = response.json().get("item") or {}
        assert item.get("scope") == "system"
        assert item.get("scope_id") is None

    def test_storage_health_present_on_success(self, admin_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("ok2.png", _image_bytes(300, 100, "PNG"), "image/png")},
            data={"segment": "corporate", "scope": "system"},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        storage_health = response.json().get("storage_health") or {}
        assert storage_health.get("status") in {"ok", "degraded"}
        assert "writable" in storage_health

    def test_dealer_cannot_upload_logo(self, dealer_token: str):
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files={"file": ("ok3.png", _image_bytes(300, 100, "PNG"), "image/png")},
            data={"segment": "corporate", "scope": "system"},
            headers={"Authorization": f"Bearer {dealer_token}"},
        )
        assert response.status_code == 403
