"""
P65 Header + Theme V2 simplification tests
- Individual header editor disabled
- Corporate header effective access dealer-scope only
- Header publish scope validation + immutable snapshot fields
- Theme override precedence and scope restrictions
"""
import hashlib
import json
import os
import uuid

import pytest
import requests


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
        pytest.skip(f"Login failed for {email}: {response.status_code} - {response.text[:200]}")
    payload = response.json()
    return payload.get("access_token") or payload.get("token")


def _headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="module")
def admin_token():
    return _login(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")


@pytest.fixture(scope="module")
def dealer_token():
    return _login(DEALER_EMAIL, DEALER_PASSWORD, "dealer")


def _create_corporate_header_draft(admin_token: str, scope: str = "system", scope_id: str | None = None):
    response = requests.post(
        f"{BASE_URL}/api/admin/ui/configs/header",
        json={
            "segment": "corporate",
            "scope": scope,
            "scope_id": scope_id,
            "status": "draft",
            "config_data": {
                "rows": [
                    {
                        "id": "row1",
                        "title": "Row1",
                        "visible": True,
                        "blocks": [
                            {"id": "logo", "type": "logo", "label": "Logo", "visible": True},
                            {"id": "search", "type": "search", "label": "Arama", "visible": True},
                        ],
                    }
                ],
                "logo": {"fallback_text": "ANNONCIA"},
            },
        },
        headers=_headers(admin_token),
    )
    assert response.status_code == 200, f"Header draft failed: {response.text[:300]}"
    item = response.json().get("item") or {}
    return item.get("id"), item.get("version")


class TestHeaderV2:
    def test_individual_header_admin_endpoints_feature_disabled(self, admin_token: str):
        scope_id = f"tenant-disabled-{uuid.uuid4().hex[:8]}"
        save_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "individual",
                "scope": "tenant",
                "scope_id": scope_id,
                "status": "draft",
                "config_data": {"rows": []},
            },
            headers=_headers(admin_token),
        )
        assert save_response.status_code == 403
        assert (save_response.json().get("detail") or {}).get("code") == "FEATURE_DISABLED"

        list_response = requests.get(
            f"{BASE_URL}/api/admin/ui/configs/header?segment=individual&scope=tenant&scope_id={scope_id}&status=draft",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert list_response.status_code == 403
        assert (list_response.json().get("detail") or {}).get("code") == "FEATURE_DISABLED"

    def test_corporate_effective_requires_dealer_scope(self, admin_token: str, dealer_token: str):
        anon_response = requests.get(f"{BASE_URL}/api/ui/header?segment=corporate")
        assert anon_response.status_code == 403
        assert (anon_response.json().get("detail") or {}).get("code") == "UNAUTHORIZED_SCOPE"

        admin_response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=corporate",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_response.status_code == 403
        assert (admin_response.json().get("detail") or {}).get("code") == "UNAUTHORIZED_SCOPE"

        dealer_response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=corporate",
            headers={"Authorization": f"Bearer {dealer_token}"},
        )
        assert dealer_response.status_code == 200

    def test_publish_scope_conflict_and_snapshot_integrity(self, admin_token: str):
        config_id, version = _create_corporate_header_draft(admin_token, "system", None)

        mismatch = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish",
            json={
                "segment": "corporate",
                "scope": "system",
                "config_id": config_id,
                "config_version": version,
                "owner_type": "dealer",
                "owner_id": "tenant-001",
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert mismatch.status_code == 409
        assert (mismatch.json().get("detail") or {}).get("code") == "SCOPE_CONFLICT"

        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish",
            json={
                "segment": "corporate",
                "scope": "system",
                "config_id": config_id,
                "config_version": version,
                "owner_type": "global",
                "owner_id": "global",
                "require_confirm": True,
            },
            headers=_headers(admin_token),
        )
        assert publish_response.status_code == 200, f"Publish failed: {publish_response.text[:300]}"
        payload = publish_response.json()
        snapshot = payload.get("snapshot") or {}
        item = payload.get("item") or {}

        assert snapshot.get("owner_type") == "global"
        assert snapshot.get("owner_id") == "global"
        assert snapshot.get("config_version") == item.get("version")
        assert isinstance(snapshot.get("resolved_config_hash"), str) and len(snapshot.get("resolved_config_hash")) == 64

        expected_hash_payload = {
            "config_type": item.get("config_type"),
            "segment": item.get("segment"),
            "scope": item.get("scope"),
            "scope_id": item.get("scope_id"),
            "config_version": item.get("version"),
            "config_data": item.get("config_data") or {},
        }
        expected_hash = hashlib.sha256(
            json.dumps(expected_hash_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        assert snapshot.get("resolved_config_hash") == expected_hash


class TestThemeOverrideV2:
    def test_invalid_scope_user_is_rejected(self, admin_token: str):
        theme_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={
                "name": f"P65 user-scope-{uuid.uuid4().hex[:8]}",
                "tokens": {
                    "colors": {"primary": "#101010", "secondary": "#202020", "accent": "#303030", "text": "#404040", "inverse": "#ffffff"},
                    "typography": {"font_family": "Poppins", "base_font_size": 16},
                    "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24},
                    "radius": {"sm": 4, "md": 8, "lg": 12},
                    "shadow": {"sm": "0 1px 2px rgba(0,0,0,0.08)", "md": "0 4px 10px rgba(0,0,0,0.12)", "lg": "0 8px 20px rgba(0,0,0,0.16)"},
                },
            },
            headers=_headers(admin_token),
        )
        assert theme_response.status_code == 200
        theme_id = theme_response.json().get("item", {}).get("id")

        assign_response = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={"theme_id": theme_id, "scope": "user", "scope_id": "user-001"},
            headers=_headers(admin_token),
        )
        assert assign_response.status_code == 400
        assert (assign_response.json().get("detail") or {}).get("code") == "INVALID_THEME_SCOPE"

    def test_dealer_override_precedence_and_resolved_snapshot(self, admin_token: str):
        global_theme_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={
                "name": f"P65 Global {uuid.uuid4().hex[:8]}",
                "tokens": {
                    "colors": {"primary": "#111111", "secondary": "#222222", "accent": "#333333", "text": "#444444", "inverse": "#ffffff"},
                    "typography": {"font_family": "Poppins", "base_font_size": 16},
                    "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24},
                    "radius": {"sm": 4, "md": 8, "lg": 12},
                    "shadow": {"sm": "0 1px 2px rgba(0,0,0,0.08)", "md": "0 4px 10px rgba(0,0,0,0.12)", "lg": "0 8px 20px rgba(0,0,0,0.16)"},
                },
            },
            headers=_headers(admin_token),
        )
        assert global_theme_response.status_code == 200
        global_theme_id = global_theme_response.json().get("item", {}).get("id")

        system_assign = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={"theme_id": global_theme_id, "scope": "system"},
            headers=_headers(admin_token),
        )
        assert system_assign.status_code == 200, f"System assignment failed: {system_assign.text[:300]}"

        dealer_theme_response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={
                "name": f"P65 Dealer {uuid.uuid4().hex[:8]}",
                "tokens": {
                    "colors": {"primary": "#aa0000", "secondary": "#222222", "accent": "#333333", "text": "#444444", "inverse": "#ffffff"},
                    "typography": {"font_family": "Poppins", "base_font_size": 16},
                    "spacing": {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24},
                    "radius": {"sm": 4, "md": 8, "lg": 12},
                    "shadow": {"sm": "0 1px 2px rgba(0,0,0,0.08)", "md": "0 4px 10px rgba(0,0,0,0.12)", "lg": "0 8px 20px rgba(0,0,0,0.16)"},
                },
            },
            headers=_headers(admin_token),
        )
        assert dealer_theme_response.status_code == 200
        dealer_theme_id = dealer_theme_response.json().get("item", {}).get("id")

        tenant_id = f"dealer-{uuid.uuid4().hex[:8]}"
        dealer_assign = requests.post(
            f"{BASE_URL}/api/admin/ui/theme-assignments",
            json={"theme_id": dealer_theme_id, "scope": "tenant", "scope_id": tenant_id},
            headers=_headers(admin_token),
        )
        assert dealer_assign.status_code == 200, f"Dealer override assign failed: {dealer_assign.text[:300]}"
        resolved_snapshot = dealer_assign.json().get("resolved_snapshot") or {}
        assert resolved_snapshot.get("owner_type") == "dealer"
        assert resolved_snapshot.get("owner_id") == tenant_id
        assert isinstance(resolved_snapshot.get("resolved_config_hash"), str)

        effective = requests.get(
            f"{BASE_URL}/api/ui/themes/effective?tenant_id={tenant_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert effective.status_code == 200, f"Effective theme failed: {effective.text[:300]}"
        data = effective.json()
        tokens = data.get("tokens") or {}
        assert data.get("source_scope") == "tenant"
        assert data.get("resolution", {}).get("precedence") == "dealer_override > global_theme"
        assert tokens.get("colors", {}).get("primary") == "#aa0000"
        assert tokens.get("colors", {}).get("secondary") == "#222222"
