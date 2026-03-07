"""
Iteration 166 Tests: P0 Regression + Faz 1 Telemetry Enhancements

P0 Regresyon:
- Kategori oluştur/düzenle/sil akışları
- Publish scope conflict ve permanent delete akışı
- RBAC temel kontrol: admin endpoint'lerine dealer erişimi

Faz 1 Backend:
- GET /api/admin/revision-redirect-telemetry response içinde:
  * success_rate_pct, failure_rate_pct, daily_trend, slo alanları
  * trend_days parametresi ile günlük trend uzunluğu doğru
"""

import os
import pytest
import requests
import uuid
from datetime import datetime, timezone

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestP0CategoryCRUDRegression:
    """P0 Regresyon: Kategori oluştur/düzenle/sil akışları"""

    @pytest.fixture
    def admin_token(self):
        """Login as admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    @pytest.fixture
    def dealer_token(self):
        """Login as dealer user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        return None

    def test_category_list_works(self, admin_token):
        """GET /api/admin/categories - list endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
            params={"limit": 10},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_category_create_and_delete(self, admin_token):
        """POST + DELETE /api/admin/categories - create and delete flow"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # First get any existing category to use as parent
        list_response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
            params={"limit": 50},
        )
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        # Find any category with module to use as parent
        parent_id = None
        module = "real_estate"
        for item in items:
            if item.get("module") == "real_estate":
                parent_id = item.get("id")
                break
        
        if not parent_id and items:
            # Fallback - use first category
            parent_id = items[0].get("id")
            module = items[0].get("module", "other")
        
        if not parent_id:
            pytest.skip("No categories found for test")
        
        # Create a test category with required sort_order
        test_slug = f"test-cat-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": f"Test Category {test_slug}",
            "slug": test_slug,
            "module": module,
            "parent_id": parent_id,
            "is_active": False,
            "sort_order": 999,  # High sort_order to not conflict
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
            json=create_payload,
        )
        assert create_response.status_code in (200, 201), f"Expected 200/201, got {create_response.status_code}: {create_response.text}"
        created = create_response.json()
        # Handle different response structures
        cat_id = created.get("id") or created.get("item", {}).get("id") or created.get("category", {}).get("id")
        assert cat_id, f"No ID in response: {created}"
        
        # Verify we can find the category in list
        verify_list_response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
            params={"limit": 100},
        )
        assert verify_list_response.status_code == 200
        found = any(item.get("id") == cat_id for item in verify_list_response.json().get("items", []))
        assert found, f"Created category {cat_id} not found in list"
        
        # Delete the test category
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/categories/{cat_id}",
            headers=headers,
        )
        assert delete_response.status_code in (200, 204), f"DELETE failed: {delete_response.status_code}: {delete_response.text}"

    def test_category_update(self, admin_token):
        """PATCH /api/admin/categories/{id} - update flow"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a category to update
        list_response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
            params={"limit": 10},
        )
        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        
        if not items:
            pytest.skip("No categories available for update test")
        
        cat = items[0]
        cat_id = cat.get("id")
        original_name = cat.get("name")
        
        # Update just the name (should not trigger slug conflict)
        update_payload = {
            "name": f"{original_name} (test)",
        }
        
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat_id}",
            headers=headers,
            json=update_payload,
        )
        assert update_response.status_code == 200, f"Update failed: {update_response.status_code}: {update_response.text}"
        
        # Revert the name
        revert_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{cat_id}",
            headers=headers,
            json={"name": original_name},
        )
        assert revert_response.status_code == 200


class TestP0PublishScopeConflictPermanentDelete:
    """P0 Regresyon: Publish scope conflict ve permanent delete akışı"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_layout_list_endpoint(self, admin_token):
        """GET /api/admin/layouts - list endpoint works"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=headers,
            params={"limit": 10, "statuses": "draft,published"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data

    def test_scope_conflict_check_endpoint(self, admin_token):
        """GET /api/admin/layouts/{revision_id} - can check revision context for scope conflict"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get a published layout
        list_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=headers,
            params={"limit": 5, "statuses": "published"},
        )
        if list_response.status_code != 200:
            pytest.skip("Could not fetch layouts")
        
        items = list_response.json().get("items", [])
        if not items:
            pytest.skip("No published layouts found")
        
        revision_id = items[0].get("id")
        
        # Fetch revision context
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts/{revision_id}",
            headers=headers,
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "item" in data
        assert "page" in data
        page = data["page"]
        assert "page_type" in page
        assert "country" in page
        assert "module" in page

    def test_permanent_delete_endpoint_structure(self, admin_token):
        """DELETE /api/admin/layouts/permanent - endpoint exists and validates"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with invalid revision_ids to verify endpoint exists
        response = requests.delete(
            f"{BASE_URL}/api/admin/layouts/permanent",
            headers=headers,
            json={"revision_ids": []},
        )
        # Should reject empty list with 422 or 400
        assert response.status_code in (400, 422), f"Expected validation error, got {response.status_code}: {response.text}"
        
        # Test with fake UUID - will get 404 because revision doesn't exist
        fake_uuid = str(uuid.uuid4())
        response2 = requests.delete(
            f"{BASE_URL}/api/admin/layouts/permanent",
            headers=headers,
            json={"revision_ids": [fake_uuid]},
        )
        # Should be 404 because revision doesn't exist
        assert response2.status_code == 404, f"Expected 404 for non-existent revision, got {response2.status_code}"


class TestP0RBACDealerBlocked:
    """P0 RBAC: Admin endpoint'lerine dealer erişimi engellenmeli"""

    @pytest.fixture(scope="class")
    def dealer_token(self):
        """Login as dealer user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "dealer@platform.com", "password": "Dealer123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Dealer login failed")

    def test_dealer_cannot_access_admin_categories(self, dealer_token):
        """Dealer should get 403 on admin category endpoints"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers=headers,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"

    def test_dealer_cannot_access_admin_layouts(self, dealer_token):
        """Dealer should get 403 on admin layout endpoints"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=headers,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"

    def test_dealer_cannot_access_revision_redirect_telemetry(self, dealer_token):
        """Dealer should get 403 on telemetry endpoint"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"

    def test_dealer_cannot_create_telemetry_event(self, dealer_token):
        """Dealer should get 403 on telemetry event creation"""
        headers = {"Authorization": f"Bearer {dealer_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry/events",
            headers=headers,
            json={"status": "success"},
        )
        assert response.status_code == 403, f"Expected 403 for dealer, got {response.status_code}"


class TestFaz1TelemetryResponse:
    """Faz 1 Backend: Telemetry response alanları doğrulama"""

    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@platform.com", "password": "Admin123!"},
        )
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin login failed")

    def test_telemetry_has_success_rate_pct(self, admin_token):
        """Response summary has success_rate_pct"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "success_rate_pct" in summary, f"Missing success_rate_pct in summary: {summary.keys()}"
        assert isinstance(summary["success_rate_pct"], (int, float))

    def test_telemetry_has_failure_rate_pct(self, admin_token):
        """Response summary has failure_rate_pct"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "failure_rate_pct" in summary, f"Missing failure_rate_pct in summary: {summary.keys()}"
        assert isinstance(summary["failure_rate_pct"], (int, float))

    def test_telemetry_has_daily_trend(self, admin_token):
        """Response summary has daily_trend array"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"trend_days": 14},
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "daily_trend" in summary, f"Missing daily_trend in summary: {summary.keys()}"
        daily_trend = summary["daily_trend"]
        assert isinstance(daily_trend, list)
        assert len(daily_trend) == 14, f"Expected 14 days, got {len(daily_trend)}"
        
        # Verify each item has required fields
        for item in daily_trend:
            assert "date" in item
            assert "total" in item
            assert "success" in item
            assert "failed" in item
            assert "failure_rate_pct" in item

    def test_telemetry_has_slo_block(self, admin_token):
        """Response summary has SLO block with targets, current, and status"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "slo" in summary, f"Missing slo in summary: {summary.keys()}"
        
        slo = summary["slo"]
        assert "targets" in slo, "Missing targets in slo"
        assert "current" in slo, "Missing current in slo"
        assert "status" in slo, "Missing status in slo"
        
        # Verify target fields
        targets = slo["targets"]
        assert "p95_latency_ms" in targets
        assert "failure_rate_pct" in targets
        
        # Verify current fields
        current = slo["current"]
        assert "p95_duration_ms" in current
        assert "failure_rate_pct" in current
        
        # Verify status fields
        status = slo["status"]
        assert "p95_latency_ok" in status
        assert "failure_rate_ok" in status

    def test_telemetry_trend_days_param(self, admin_token):
        """trend_days parameter controls daily_trend length"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test with 7 days
        response_7 = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"trend_days": 7},
        )
        assert response_7.status_code == 200
        trend_7 = response_7.json().get("summary", {}).get("daily_trend", [])
        assert len(trend_7) == 7, f"Expected 7 days, got {len(trend_7)}"
        
        # Test with 30 days
        response_30 = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
            params={"trend_days": 30},
        )
        assert response_30.status_code == 200
        trend_30 = response_30.json().get("summary", {}).get("daily_trend", [])
        assert len(trend_30) == 30, f"Expected 30 days, got {len(trend_30)}"

    def test_telemetry_has_failure_reason_counts(self, admin_token):
        """Response summary has failure_reason_counts"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "failure_reason_counts" in summary, f"Missing failure_reason_counts"
        assert isinstance(summary["failure_reason_counts"], dict)

    def test_telemetry_has_duration_histogram(self, admin_token):
        """Response summary has duration_histogram with correct buckets"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(
            f"{BASE_URL}/api/admin/revision-redirect-telemetry",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        summary = data.get("summary", {})
        assert "duration_histogram" in summary
        
        histogram = summary["duration_histogram"]
        expected_buckets = ["0_250", "251_500", "501_1000", "1001_2000", "2001_plus"]
        for bucket in expected_buckets:
            assert bucket in histogram, f"Missing bucket {bucket} in histogram"
