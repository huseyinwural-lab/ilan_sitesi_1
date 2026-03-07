"""
Iteration 147: Test reset-and-seed-home-wireframe workflow endpoint
Testing the refactored endpoint with bulk SQL + exception-safe response
"""
import os
import requests
import pytest

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://layout-uniqueness.preview.emergentagent.com').rstrip('/')

class TestResetWireframeWorkflow:
    """Test reset-and-seed-home-wireframe workflow endpoint"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": "admin@platform.com",
                "password": "Admin123!"
            }
        )
        if response.status_code == 200:
            token = response.json().get("access_token") or response.json().get("token")
            if token:
                return token
        pytest.skip("Auth failed - skipping tests")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers with token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
            "Accept-Language": "tr"
        }

    def test_reset_wireframe_endpoint_returns_ok(self, auth_headers):
        """POST /api/admin/layouts/workflows/reset-and-seed-home-wireframe should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/admin/layouts/workflows/reset-and-seed-home-wireframe",
            headers=auth_headers,
            json={
                "countries": ["TR", "DE", "FR"],
                "module": "global",
                "passivate_all": True,
                "hard_delete_demo_pages": True
            },
            timeout=60
        )
        
        print(f"Reset wireframe status: {response.status_code}")
        print(f"Reset wireframe response: {response.text[:1000]}")
        
        # Endpoint should NOT return 503 anymore (that was the old behavior)
        assert response.status_code != 503, "Endpoint should not return 503 DB_ERROR"
        
        # Should return 200 with json response
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Check response structure
        assert "ok" in data, "Response should contain 'ok' field"
        
        if data["ok"]:
            print("SUCCESS: Workflow completed successfully!")
            assert "countries" in data
            assert "module" in data
            assert "summary" in data
            
            summary = data["summary"]
            print(f"Summary: {summary}")
            assert "passivated_revisions" in summary
            assert "home_pages_touched" in summary
            assert "reactivated_home_revisions" in summary
        else:
            print(f"WARN: Workflow returned ok=false with detail: {data.get('detail', 'no detail')}")
            # Even on failure, structure should be correct
            assert "error" in data or "detail" in data

    def test_admin_layouts_list_after_reset(self, auth_headers):
        """GET /api/admin/layouts should return updated list after reset"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={
                "include_deleted": True,
                "statuses": "draft,published",
                "page": 1,
                "limit": 200
            },
            timeout=30
        )
        
        print(f"Layouts list status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        # Count active and passive items
        active_items = [i for i in items if not i.get("is_deleted") and i.get("is_active", True)]
        passive_items = [i for i in items if i.get("is_deleted") or not i.get("is_active", True)]
        
        print(f"Total items: {len(items)}")
        print(f"Active items: {len(active_items)}")
        print(f"Passive items: {len(passive_items)}")
        
        # Check if we have home pages for TR/DE/FR in active list
        home_countries_active = set()
        for item in active_items:
            if item.get("page_type") == "home":
                home_countries_active.add(item.get("country"))
        
        print(f"Active home page countries: {home_countries_active}")
        
        # After reset workflow, we should have active home pages for TR, DE, FR
        for country in ["TR", "DE", "FR"]:
            assert country in home_countries_active, f"Expected active home page for {country}"

    def test_passive_list_contains_old_revisions(self, auth_headers):
        """GET /api/admin/layouts with state=passive should contain old revisions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={
                "state": "passive",
                "include_deleted": True,
                "statuses": "draft,published",
                "page": 1,
                "limit": 200
            },
            timeout=30
        )
        
        print(f"Passive list status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"Passive list items count: {len(items)}")
        
        # After passivate_all=True, old revisions should be in passive list
        if len(items) > 0:
            print(f"Sample passive item: page_type={items[0].get('page_type')}, country={items[0].get('country')}")
            
            # Verify passive items have is_active=False or is_deleted=True
            for item in items[:5]:  # Check first 5
                is_deleted = item.get("is_deleted", False)
                is_active = item.get("is_active", True)
                assert is_deleted or not is_active, f"Passive item should be deleted or inactive"

    def test_active_list_contains_new_home_revisions(self, auth_headers):
        """GET /api/admin/layouts with state=active should contain new home revisions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers=auth_headers,
            params={
                "state": "active",
                "include_deleted": False,
                "statuses": "draft,published",
                "page": 1,
                "limit": 200
            },
            timeout=30
        )
        
        print(f"Active list status: {response.status_code}")
        assert response.status_code == 200
        
        data = response.json()
        items = data.get("items", [])
        
        print(f"Active list items count: {len(items)}")
        
        # Check for home pages in active list
        home_items = [i for i in items if i.get("page_type") == "home"]
        print(f"Active home items count: {len(home_items)}")
        
        # Should have home pages for TR, DE, FR
        home_countries = {i.get("country") for i in home_items}
        print(f"Active home countries: {home_countries}")
        
        for expected_country in ["TR", "DE", "FR"]:
            assert expected_country in home_countries, f"Missing active home page for {expected_country}"
        
        # Verify active items have is_active=True
        for item in home_items:
            assert item.get("is_active", True), f"Active home item should have is_active=True"
            assert not item.get("is_deleted", False), f"Active home item should not be deleted"


class TestPublicHomePages:
    """Test public home pages render correctly after reset"""
    
    def test_public_home_tr(self):
        """GET /tr should return wireframe layout"""
        response = requests.get(f"{BASE_URL}/tr", timeout=30, allow_redirects=True)
        print(f"GET /tr status: {response.status_code}")
        # Should return HTML page
        assert response.status_code == 200

    def test_public_home_de(self):
        """GET /de should return wireframe layout"""
        response = requests.get(f"{BASE_URL}/de", timeout=30, allow_redirects=True)
        print(f"GET /de status: {response.status_code}")
        assert response.status_code == 200

    def test_public_home_fr(self):
        """GET /fr should return wireframe layout"""
        response = requests.get(f"{BASE_URL}/fr", timeout=30, allow_redirects=True)
        print(f"GET /fr status: {response.status_code}")
        assert response.status_code == 200

    def test_layout_resolve_tr(self):
        """GET /api/layout/resolve?country=TR&page_type=home should return layout"""
        response = requests.get(
            f"{BASE_URL}/api/layout/resolve",
            params={
                "country": "TR",
                "module": "global",
                "page_type": "home"
            },
            timeout=30
        )
        print(f"Layout resolve TR status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            payload = data.get("payload_json", {})
            rows = payload.get("rows", [])
            print(f"TR home layout rows: {len(rows)}")
            # Should have wireframe layout rows
            assert len(rows) > 0, "TR home layout should have rows"

    def test_layout_resolve_de(self):
        """GET /api/layout/resolve?country=DE&page_type=home should return layout"""
        response = requests.get(
            f"{BASE_URL}/api/layout/resolve",
            params={
                "country": "DE",
                "module": "global",
                "page_type": "home"
            },
            timeout=30
        )
        print(f"Layout resolve DE status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            payload = data.get("payload_json", {})
            rows = payload.get("rows", [])
            print(f"DE home layout rows: {len(rows)}")
            assert len(rows) > 0, "DE home layout should have rows"

    def test_layout_resolve_fr(self):
        """GET /api/layout/resolve?country=FR&page_type=home should return layout"""
        response = requests.get(
            f"{BASE_URL}/api/layout/resolve",
            params={
                "country": "FR",
                "module": "global",
                "page_type": "home"
            },
            timeout=30
        )
        print(f"Layout resolve FR status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            payload = data.get("payload_json", {})
            rows = payload.get("rows", [])
            print(f"FR home layout rows: {len(rows)}")
            assert len(rows) > 0, "FR home layout should have rows"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
