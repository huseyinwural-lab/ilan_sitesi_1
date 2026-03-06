import uuid

import requests


BASE_URL = "https://page-builder-227.preview.emergentagent.com"

CREDS = {
    "super_admin": {"email": "admin@platform.com", "password": "Admin123!"},
    "country_admin": {"email": "countryadmin@platform.com", "password": "Country123!"},
    "admin": {"email": "admin_view@platform.com", "password": "AdminView123!"},
}


def _login(role: str) -> str:
    payload = CREDS[role]
    response = requests.post(f"{BASE_URL}/api/auth/login", json=payload, timeout=30)
    assert response.status_code == 200, f"login failed for {role}: {response.text}"
    token = response.json().get("access_token")
    assert token, f"access_token missing for {role}"
    return token


def _headers(role: str):
    return {"Authorization": f"Bearer {_login(role)}"}


def test_permission_migration_endpoint_super_admin_only():
    super_headers = _headers("super_admin")
    admin_headers = _headers("admin")

    ok_response = requests.post(
        f"{BASE_URL}/api/admin/permissions/migrate-from-roles",
        headers=super_headers,
        timeout=60,
    )
    assert ok_response.status_code == 200, ok_response.text

    denied_response = requests.post(
        f"{BASE_URL}/api/admin/permissions/migrate-from-roles",
        headers=admin_headers,
        timeout=30,
    )
    assert denied_response.status_code == 403, denied_response.text


def test_permissions_snapshot_super_admin_only():
    super_headers = _headers("super_admin")
    country_headers = _headers("country_admin")

    ok_response = requests.get(
        f"{BASE_URL}/api/admin/permissions/snapshot",
        headers=super_headers,
        timeout=30,
    )
    assert ok_response.status_code == 200, ok_response.text
    payload = ok_response.json()
    assert "count" in payload
    assert "items" in payload

    denied_response = requests.get(
        f"{BASE_URL}/api/admin/permissions/snapshot",
        headers=country_headers,
        timeout=30,
    )
    assert denied_response.status_code == 403, denied_response.text


def test_permissions_me_returns_finance_content_domains():
    response = requests.get(
        f"{BASE_URL}/api/admin/permissions/me",
        headers=_headers("admin"),
        timeout=30,
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    domains = payload.get("domains", {})
    assert "finance" in domains
    assert "content" in domains
    assert domains["finance"].get("view") is True
    assert domains["finance"].get("export") is False


def test_content_publish_blocked_for_admin():
    response = requests.post(
        f"{BASE_URL}/api/admin/info-pages",
        headers=_headers("admin"),
        json={
            "slug": f"perm-test-{uuid.uuid4().hex[:8]}",
            "title_tr": "perm",
            "title_de": "perm",
            "title_fr": "perm",
            "content_tr": "perm",
            "content_de": "perm",
            "content_fr": "perm",
            "is_published": True,
        },
        timeout=30,
    )
    assert response.status_code == 403, response.text


def test_finance_export_allowed_for_country_admin_but_edit_denied():
    export_response = requests.get(
        f"{BASE_URL}/api/admin/payments/export/csv",
        headers=_headers("country_admin"),
        timeout=30,
    )
    assert export_response.status_code == 200, export_response.text

    edit_response = requests.post(
        f"{BASE_URL}/api/admin/plans",
        headers=_headers("country_admin"),
        json={
            "name": "perm-edit-test",
            "slug": f"perm-edit-{uuid.uuid4().hex[:8]}",
            "country_scope": "global",
            "period": "monthly",
            "price_amount": 10,
            "currency_code": "EUR",
            "listing_quota": 1,
            "showcase_quota": 0,
            "active_flag": True,
        },
        timeout=30,
    )
    assert edit_response.status_code == 403, edit_response.text