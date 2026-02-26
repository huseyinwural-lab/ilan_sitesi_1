"""
P1.2 External Meilisearch Activation + P1.3 Facet/Dynamic Sidebar Tests
Tests external Meili activation, health, reindex, stage-smoke, sync-jobs,
and v2/search facet_meta + facets.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
        timeout=15,
    )
    if res.status_code != 200:
        pytest.skip("Admin login failed - skipping test suite")
    return res.json()["access_token"]


@pytest.fixture(scope="module")
def user_token():
    """Get user authentication token"""
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User123!"},
        timeout=15,
    )
    if res.status_code != 200:
        pytest.skip("User login failed - skipping test suite")
    return res.json()["access_token"]


class TestP12ExternalMeiliActivation:
    """P1.2 External activation verification tests"""

    def test_meili_health_pass_no_config_required_error(self, admin_token):
        """
        /api/admin/search/meili/health PASS, ACTIVE_CONFIG_REQUIRED yok
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/health",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        # External config should be active
        assert data.get("ok") is True, f"Expected ok=true, got {data}"
        assert "ACTIVE_CONFIG_REQUIRED" not in res.text
        # Check health details
        health = data.get("health", {})
        assert health.get("status") == "PASS" or health.get("ok") is True
        # Check index info present
        assert data.get("active_index") is not None
        assert data.get("active_url") is not None

    def test_admin_health_detail_meili_connected(self, admin_token):
        """
        /api/admin/system/health-detail içinde meili.connected true
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/system/health-detail",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        meili = data.get("meili", {})
        assert meili.get("configured") is True, "meili.configured should be true"
        assert meili.get("connected") is True, "meili.connected should be true"
        assert meili.get("status") == "connected"
        assert meili.get("url") is not None
        assert meili.get("index_name") is not None

    def test_stage_smoke_ranking_sort_hits(self, admin_token):
        """
        /api/admin/search/meili/stage-smoke returns 200 + ranking_sort + hits
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/stage-smoke?q=",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("ok") is True
        # ranking_sort should be present
        assert "ranking_sort" in data
        ranking_sort = data["ranking_sort"]
        assert isinstance(ranking_sort, list)
        assert "premium_score:desc" in ranking_sort or "published_at:desc" in ranking_sort
        # hits should be present
        assert "hits" in data
        hits = data["hits"]
        assert isinstance(hits, list)
        # index_document_count should be present
        assert "index_document_count" in data

    def test_bulk_reindex_returns_indexed_docs(self, admin_token):
        """
        /api/admin/search/meili/reindex returns indexed_docs + index_document_count
        """
        res = requests.post(
            f"{BASE_URL}/api/admin/search/meili/reindex",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"chunk_size": 50, "max_docs": 5, "reset_index": False},
            timeout=30,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert data.get("ok") is True
        assert "indexed_docs" in data
        assert isinstance(data["indexed_docs"], int)
        assert "index_document_count" in data
        assert isinstance(data["index_document_count"], int)
        assert "elapsed_seconds" in data

    def test_sync_jobs_metrics_no_dead_letter(self, admin_token):
        """
        /api/admin/search/meili/sync-jobs metrics dead_letter=0 and no failed processing
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?limit=100",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        metrics = data.get("metrics", {})
        # dead_letter should be 0 or not present
        dead_letter_count = metrics.get("dead_letter", 0)
        assert dead_letter_count == 0, f"Expected dead_letter=0, got {dead_letter_count}"
        # Items should have status in valid states
        items = data.get("items", [])
        for item in items:
            status = item.get("status")
            assert status in {"pending", "processing", "retry", "done", "dead_letter"}

    def test_sync_jobs_filter_status(self, admin_token):
        """
        Test sync-jobs status filter works correctly
        """
        for status in ["done", "pending"]:
            res = requests.get(
                f"{BASE_URL}/api/admin/search/meili/sync-jobs?status={status}&limit=10",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=15,
            )
            assert res.status_code == 200, f"Expected 200 for status={status}, got {res.status_code}"
            data = res.json()
            # All items should have the filtered status (if any)
            items = data.get("items", [])
            for item in items:
                assert item.get("status") == status, f"Expected status={status}, got {item.get('status')}"


class TestEventDrivenSyncTriggers:
    """
    Event-driven sync live tests: verify sync job triggers exist for
    publish, unpublish, soft-delete operations.
    """

    def test_sync_jobs_have_expected_triggers(self, admin_token):
        """
        Verify sync jobs contain expected triggers for listing lifecycle operations
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200
        data = res.json()
        items = data.get("items", [])
        
        # Collect all triggers
        triggers = set()
        for item in items:
            trigger = item.get("trigger")
            if trigger:
                triggers.add(trigger)
        
        # Check at least some expected triggers exist
        expected_triggers = {"listing_create", "listing_request_publish", "moderation_approve"}
        found_triggers = triggers & expected_triggers
        assert len(found_triggers) > 0, f"Expected at least one of {expected_triggers}, found {triggers}"

    def test_sync_jobs_operations_valid(self, admin_token):
        """
        All sync job operations should be 'upsert' or 'delete'
        """
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?limit=30",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert res.status_code == 200
        data = res.json()
        items = data.get("items", [])
        for item in items:
            operation = item.get("operation")
            assert operation in {"upsert", "delete"}, f"Invalid operation: {operation}"


class TestP13V2SearchFacets:
    """P1.3 backend: /api/v2/search facet_meta + facets tests"""

    def test_v2_search_returns_facet_meta_and_facets(self):
        """
        /api/v2/search facet_meta + facets returns for filterable attributes
        - Without category, facets may be empty (no filterable attrs mapped)
        - Structure should still be present
        """
        res = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&page=1&limit=10",
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        # facet_meta and facets keys must exist
        assert "facet_meta" in data, "facet_meta key missing in response"
        assert "facets" in data, "facets key missing in response"
        # pagination must exist
        assert "pagination" in data
        assert "items" in data

    def test_v2_search_pagination_total_updates(self):
        """
        v2/search pagination total updates with filters
        """
        # Without filters
        res1 = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&page=1&limit=5",
            timeout=15,
        )
        assert res1.status_code == 200
        data1 = res1.json()
        total_no_filter = data1.get("pagination", {}).get("total", 0)
        
        # With price filter (might reduce results)
        res2 = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&page=1&limit=5&price_min=1000&price_max=50000",
            timeout=15,
        )
        assert res2.status_code == 200
        data2 = res2.json()
        total_with_filter = data2.get("pagination", {}).get("total", 0)
        
        # With very restrictive filter, total should be <= no filter
        assert total_with_filter <= total_no_filter, "Price filter didn't reduce results"

    def test_v2_search_sort_options(self):
        """
        v2/search sort parameter works: price_asc, price_desc, date_asc, date_desc
        """
        for sort_key in ["price_asc", "price_desc", "date_asc", "date_desc"]:
            res = requests.get(
                f"{BASE_URL}/api/v2/search?country=DE&page=1&limit=3&sort={sort_key}",
                timeout=15,
            )
            assert res.status_code == 200, f"Sort {sort_key} failed: {res.status_code}"
            data = res.json()
            assert "items" in data

    def test_v2_search_with_category_filter(self):
        """
        v2/search with category parameter filters results
        """
        # Get a category first
        cat_res = requests.get(
            f"{BASE_URL}/api/categories?module=vehicle&country=DE",
            timeout=15,
        )
        if cat_res.status_code != 200:
            pytest.skip("Could not fetch categories")
        
        categories = cat_res.json()
        if not categories:
            pytest.skip("No categories available")
        
        category_id = categories[0].get("id")
        res = requests.get(
            f"{BASE_URL}/api/v2/search?country=DE&category={category_id}&page=1&limit=5",
            timeout=15,
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "items" in data
        assert "pagination" in data


class TestRBACProtection:
    """Verify admin endpoints are RBAC protected"""

    def test_meili_health_requires_admin(self, user_token):
        """Non-admin should get 403"""
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/health",
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=15,
        )
        assert res.status_code == 403, f"Expected 403 for user, got {res.status_code}"

    def test_meili_reindex_requires_admin(self, user_token):
        """Non-admin should get 403"""
        res = requests.post(
            f"{BASE_URL}/api/admin/search/meili/reindex",
            headers={"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
            json={"chunk_size": 50},
            timeout=15,
        )
        assert res.status_code == 403, f"Expected 403 for user, got {res.status_code}"

    def test_unauthenticated_gets_401(self):
        """No auth header should get 401"""
        res = requests.get(
            f"{BASE_URL}/api/admin/search/meili/health",
            timeout=15,
        )
        assert res.status_code == 401, f"Expected 401 without auth, got {res.status_code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
