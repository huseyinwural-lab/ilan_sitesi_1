import os
import time

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def _request(method: str, url: str, **kwargs):
    request_timeout = kwargs.pop("timeout", 30)
    last_error = None
    for attempt in range(4):
        try:
            return requests.request(method, url, timeout=request_timeout, **kwargs)
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt >= 3:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise last_error


def _login(email: str, password: str):
    response = _request(
        "POST",
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if response.status_code != 200:
        return None
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    token = _login("admin@platform.com", "Admin123!")
    if not token:
        pytest.skip("admin login failed")
    return token


def _headers(token: str):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _create_category(token: str, *, name: str, slug: str, module: str, country_code: str, sort_order: int, parent_id: str | None = None):
    payload = {
        "name": name,
        "slug": slug,
        "module": module,
        "country_code": country_code,
        "sort_order": sort_order,
        "active_flag": True,
        "parent_id": parent_id,
    }
    response = _request(
        "POST",
        f"{BASE_URL}/api/admin/categories",
        headers=_headers(token),
        json=payload,
        timeout=30,
    )
    assert response.status_code in {200, 201}, response.text
    return (response.json() or {}).get("category") or {}


class TestCategoryDeleteCascade:
    def test_delete_cascade_soft_deletes_all_descendants(self, admin_token):
        suffix = str(int(time.time() * 1000))
        parent = _create_category(
            admin_token,
            name=f"Cascade Parent {suffix}",
            slug=f"cascade-parent-{suffix}",
            module="other",
            country_code="TR",
            sort_order=9990,
        )
        child = _create_category(
            admin_token,
            name=f"Cascade Child {suffix}",
            slug=f"cascade-child-{suffix}",
            module="other",
            country_code="TR",
            sort_order=1,
            parent_id=parent.get("id"),
        )
        grandchild = _create_category(
            admin_token,
            name=f"Cascade Grandchild {suffix}",
            slug=f"cascade-grandchild-{suffix}",
            module="other",
            country_code="TR",
            sort_order=1,
            parent_id=child.get("id"),
        )

        delete_response = _request(
            "DELETE",
            f"{BASE_URL}/api/admin/categories/{parent.get('id')}",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"cascade": "true"},
            timeout=30,
        )
        assert delete_response.status_code == 200, delete_response.text
        payload = delete_response.json()
        deleted_ids = set(payload.get("deleted_ids") or [])

        assert payload.get("cascade") is True
        assert int(payload.get("deleted_count") or 0) >= 3
        assert payload.get("undo_operation_id")
        assert payload.get("undo_expires_at")
        assert parent.get("id") in deleted_ids
        assert child.get("id") in deleted_ids
        assert grandchild.get("id") in deleted_ids

        list_response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"country": "TR", "module": "other"},
            timeout=30,
        )
        assert list_response.status_code == 200, list_response.text
        ids = {str(item.get("id")) for item in ((list_response.json() or {}).get("items") or [])}
        assert parent.get("id") not in ids
        assert child.get("id") not in ids
        assert grandchild.get("id") not in ids

        undo_response = _request(
            "POST",
            f"{BASE_URL}/api/admin/categories/delete-operations/{payload.get('undo_operation_id')}/undo",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        assert undo_response.status_code == 200, undo_response.text
        undo_payload = undo_response.json()
        assert undo_payload.get("ok") is True
        assert int(undo_payload.get("restored_count") or 0) >= 3

        restored_list_response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"country": "TR", "module": "other"},
            timeout=30,
        )
        assert restored_list_response.status_code == 200, restored_list_response.text
        restored_ids = {str(item.get("id")) for item in ((restored_list_response.json() or {}).get("items") or [])}
        assert parent.get("id") in restored_ids
        assert child.get("id") in restored_ids
        assert grandchild.get("id") in restored_ids

        history_response = _request(
            "GET",
            f"{BASE_URL}/api/admin/categories/delete-operations",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"hours": 24, "limit": 20},
            timeout=30,
        )
        assert history_response.status_code == 200, history_response.text
        history_items = (history_response.json() or {}).get("items") or []
        operation_ids = {str(item.get("operation_id")) for item in history_items}
        assert str(payload.get("undo_operation_id")) in operation_ids

    def test_delete_invalid_id_returns_structured_error(self, admin_token):
        response = _request(
            "DELETE",
            f"{BASE_URL}/api/admin/categories/not-a-valid-id",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30,
        )
        assert response.status_code == 400, response.text
        detail = (response.json() or {}).get("detail") or {}
        assert detail.get("error_code") == "CATEGORY_ID_INVALID"
        assert detail.get("field_name") == "category_id"
