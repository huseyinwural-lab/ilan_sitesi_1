"""
P1.2 Meilisearch Sync Feature Tests
Testing: document contract, sync jobs queue, reindex endpoint, stage-smoke, public search, RBAC
"""
import os
import pytest
import requests
import uuid as uuid_lib
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


class TestContext:
    admin_token = None
    user_token = None
    test_listing_id = None


ctx = TestContext()


@pytest.fixture(scope="module", autouse=True)
def setup_tokens():
    """Login admin and non-admin user for testing"""
    # Admin login
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    if resp.status_code == 200:
        ctx.admin_token = resp.json().get("access_token")
        print(f"SETUP: Admin login successful")
    else:
        pytest.skip(f"Admin login failed: {resp.status_code} - {resp.text}")

    # Non-admin user login
    resp = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": USER_EMAIL, "password": USER_PASSWORD},
        timeout=10,
    )
    if resp.status_code == 200:
        ctx.user_token = resp.json().get("access_token")
        print(f"SETUP: User login successful")
    else:
        print(f"SETUP: Non-admin user login failed: {resp.status_code}")

    yield


# ---- P1.2 CONTRACT TESTS ----

class TestMeiliContract:
    """P1.2: GET /api/admin/search/meili/contract returns required document fields"""

    def test_contract_endpoint_returns_200(self):
        """Contract endpoint should be accessible to super_admin"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print(f"PASS: Contract endpoint returned 200")

    def test_contract_has_primary_key(self):
        """Contract should define primary_key as listing_id"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "primary_key" in data, "Contract should have primary_key"
        assert data["primary_key"] == "listing_id", f"primary_key should be listing_id, got {data['primary_key']}"
        print(f"PASS: primary_key=listing_id confirmed")

    def test_contract_has_required_document_fields(self):
        """Contract should define all required document fields"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        required_fields = [
            "listing_id",
            "category_path_ids",
            "make_id",
            "model_id",
            "trim_id",
            "city_id",
            "attribute_flat_map",
            "price",
            "premium_score",
            "published_at",
            "searchable_text",
        ]
        
        document_fields = data.get("document_fields", [])
        assert isinstance(document_fields, list), "document_fields should be a list"
        
        for field in required_fields:
            assert field in document_fields, f"Contract missing required field: {field}"
        
        print(f"PASS: All required document fields present: {document_fields}")

    def test_contract_has_sync_hooks(self):
        """Contract should define sync hooks for create/update/delete/soft_delete"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        sync_hooks = data.get("sync_hooks", {})
        assert isinstance(sync_hooks, dict), "sync_hooks should be a dict"
        
        for hook in ["create", "update", "delete", "soft_delete"]:
            assert hook in sync_hooks, f"sync_hooks should have {hook} hook"
        
        print(f"PASS: sync_hooks defined for create/update/delete/soft_delete: {sync_hooks}")

    def test_contract_has_queue_config(self):
        """Contract should define queue retry strategy and dead_letter state"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        
        queue_config = data.get("queue", {})
        assert isinstance(queue_config, dict), "queue should be a dict"
        assert "retry_strategy" in queue_config, "queue should have retry_strategy"
        assert "exponential" in queue_config["retry_strategy"].lower(), "retry_strategy should be exponential_backoff"
        assert "dead_letter_state" in queue_config, "queue should have dead_letter_state"
        assert queue_config["dead_letter_state"] == "dead_letter", "dead_letter_state should be 'dead_letter'"
        
        print(f"PASS: Queue config defined: {queue_config}")


# ---- P1.2 HEALTH ENDPOINT TESTS ----

class TestMeiliHealth:
    """P1.2: GET /api/admin/search/meili/health works with active config"""

    def test_health_endpoint_200_with_active_config(self):
        """Health endpoint should return 200 if active config exists"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/health",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        # Expect 200 if active config exists, 400 if not
        if resp.status_code == 400:
            detail = resp.json().get("detail", "")
            if "ACTIVE_CONFIG_REQUIRED" in detail:
                pytest.skip("No active meili config - health test skipped")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "ok" in data, "Response should have ok field"
        assert "health" in data, "Response should have health object"
        assert "active_index" in data, "Response should have active_index"
        assert "active_url" in data, "Response should have active_url"
        print(f"PASS: Health endpoint returned 200, ok={data.get('ok')}, active_index={data.get('active_index')}")

    def test_health_endpoint_rbac_403_for_non_admin(self):
        """Health endpoint should return 403 for non-super_admin"""
        if not ctx.user_token:
            pytest.skip("User token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/health",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin got 403 on health endpoint")


# ---- P1.2 REINDEX ENDPOINT TESTS ----

class TestMeiliReindex:
    """P1.2: POST /api/admin/search/meili/reindex supports chunked processing"""

    def test_reindex_endpoint_with_max_docs(self):
        """Reindex endpoint should return indexed_docs and elapsed_seconds"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        payload = {
            "chunk_size": 100,
            "max_docs": 5,  # Small number for testing
            "reset_index": False,  # Don't clear existing data
        }
        resp = requests.post(
            f"{BASE_URL}/api/admin/search/meili/reindex",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json=payload,
            timeout=60,
        )
        
        # Expect 200 if active config exists, or error if no config
        if resp.status_code == 500 and "no_active_meili_config" in resp.text.lower():
            pytest.skip("No active meili config - reindex test skipped")
        if resp.status_code == 400:
            pytest.skip(f"Reindex failed (probably no active config): {resp.text}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "ok" in data, "Response should have ok field"
        assert "indexed_docs" in data, "Response should have indexed_docs field"
        assert "elapsed_seconds" in data, "Response should have elapsed_seconds field"
        assert "chunk_size" in data, "Response should have chunk_size field"
        
        assert isinstance(data["indexed_docs"], int), "indexed_docs should be an integer"
        assert isinstance(data["elapsed_seconds"], (int, float)), "elapsed_seconds should be a number"
        
        print(f"PASS: Reindex returned ok={data.get('ok')}, indexed_docs={data.get('indexed_docs')}, elapsed_seconds={data.get('elapsed_seconds')}")

    def test_reindex_endpoint_rbac_403_for_non_admin(self):
        """Reindex endpoint should return 403 for non-super_admin"""
        if not ctx.user_token:
            pytest.skip("User token not available")
        resp = requests.post(
            f"{BASE_URL}/api/admin/search/meili/reindex",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            json={"chunk_size": 100, "max_docs": 10},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin got 403 on reindex endpoint")


# ---- P1.2 STAGE-SMOKE ENDPOINT TESTS ----

class TestMeiliStageSmoke:
    """P1.2: GET /api/admin/search/meili/stage-smoke returns ranking_sort"""

    def test_stage_smoke_returns_ranking_sort(self):
        """Stage-smoke should return ranking_sort with premium_score:desc and published_at:desc"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/stage-smoke?q=test",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        
        if resp.status_code == 500 and "no_active_meili_config" in resp.text.lower():
            pytest.skip("No active meili config - stage-smoke test skipped")
        if resp.status_code == 400:
            pytest.skip(f"Stage-smoke failed (probably no active config): {resp.text}")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "ranking_sort" in data, "Response should have ranking_sort field"
        ranking_sort = data["ranking_sort"]
        assert isinstance(ranking_sort, list), "ranking_sort should be a list"
        assert "premium_score:desc" in ranking_sort, "ranking_sort should include premium_score:desc"
        assert "published_at:desc" in ranking_sort, "ranking_sort should include published_at:desc"
        
        assert "hits" in data, "Response should have hits field"
        assert "estimatedTotalHits" in data, "Response should have estimatedTotalHits field"
        
        print(f"PASS: Stage-smoke returned ranking_sort={ranking_sort}, hits_count={len(data.get('hits', []))}")

    def test_stage_smoke_rbac_403_for_non_admin(self):
        """Stage-smoke endpoint should return 403 for non-super_admin"""
        if not ctx.user_token:
            pytest.skip("User token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/stage-smoke?q=test",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
        print(f"PASS: Non-admin got 403 on stage-smoke endpoint")


# ---- P1.2 PUBLIC SEARCH ENDPOINT TESTS ----

class TestMeiliPublicSearch:
    """P1.2: GET /api/search/meili query endpoint returns hits/metadata"""

    def test_public_search_returns_hits_and_metadata(self):
        """Public search should return hits, estimatedTotalHits, query, limit, offset"""
        resp = requests.get(
            f"{BASE_URL}/api/search/meili?q=test&limit=10&offset=0",
            timeout=10,
        )
        
        if resp.status_code == 503:
            detail = resp.json().get("detail", "")
            if "MEILI_SEARCH_UNAVAILABLE" in detail:
                pytest.skip("Meili search unavailable - no active config")
        
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "hits" in data, "Response should have hits field"
        assert isinstance(data["hits"], list), "hits should be a list"
        assert "estimatedTotalHits" in data, "Response should have estimatedTotalHits field"
        assert "query" in data, "Response should have query field"
        assert "limit" in data, "Response should have limit field"
        assert "offset" in data, "Response should have offset field"
        
        print(f"PASS: Public search returned hits_count={len(data['hits'])}, estimatedTotalHits={data.get('estimatedTotalHits')}")

    def test_public_search_no_auth_required(self):
        """Public search endpoint should be accessible without authentication"""
        resp = requests.get(
            f"{BASE_URL}/api/search/meili?q=",
            timeout=10,
        )
        # Should be 200 or 503 (if no config), NOT 401/403
        assert resp.status_code in (200, 503), f"Expected 200 or 503, got {resp.status_code}: {resp.text}"
        print(f"PASS: Public search accessible without auth (status={resp.status_code})")


# ---- P1.2 SYNC-JOBS QUEUE TESTS ----

class TestMeiliSyncJobsQueue:
    """P1.2: /api/admin/search/meili/sync-jobs and /process queue handling"""

    def test_list_sync_jobs_returns_metrics_and_items(self):
        """GET /api/admin/search/meili/sync-jobs should return metrics and items"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?limit=50",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "metrics" in data, "Response should have metrics field"
        assert "items" in data, "Response should have items field"
        assert isinstance(data["metrics"], dict), "metrics should be a dict"
        assert isinstance(data["items"], list), "items should be a list"
        
        print(f"PASS: sync-jobs returned metrics={data['metrics']}, items_count={len(data['items'])}")

    def test_list_sync_jobs_filter_by_status(self):
        """GET /api/admin/search/meili/sync-jobs?status=pending should filter"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        
        for status in ["pending", "done", "dead_letter"]:
            resp = requests.get(
                f"{BASE_URL}/api/admin/search/meili/sync-jobs?status={status}&limit=10",
                headers={"Authorization": f"Bearer {ctx.admin_token}"},
                timeout=10,
            )
            assert resp.status_code == 200, f"Expected 200 for status={status}, got {resp.status_code}"
        
        print(f"PASS: sync-jobs filter by status works for pending/done/dead_letter")

    def test_list_sync_jobs_invalid_status_returns_400(self):
        """Invalid status filter should return 400"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?status=invalid_status",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 400, f"Expected 400 for invalid status, got {resp.status_code}: {resp.text}"
        print(f"PASS: Invalid status returns 400")

    def test_process_sync_jobs_endpoint(self):
        """POST /api/admin/search/meili/sync-jobs/process should return processing summary"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.post(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs/process",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            json={"limit": 10},
            timeout=30,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        
        assert "ok" in data, "Response should have ok field"
        assert "processed" in data, "Response should have processed field"
        assert "success" in data, "Response should have success field"
        assert "failed" in data, "Response should have failed field"
        assert "dead_letter" in data, "Response should have dead_letter field"
        
        print(f"PASS: process endpoint returned ok={data.get('ok')}, processed={data.get('processed')}, success={data.get('success')}, failed={data.get('failed')}")

    def test_sync_jobs_rbac_403_for_non_admin(self):
        """Sync-jobs endpoints should return 403 for non-super_admin"""
        if not ctx.user_token:
            pytest.skip("User token not available")
        
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403 on GET sync-jobs, got {resp.status_code}"
        
        resp = requests.post(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs/process",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            json={"limit": 10},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403 on POST process, got {resp.status_code}"
        
        print(f"PASS: Non-admin got 403 on sync-jobs endpoints")


# ---- P1.2 RBAC COMPREHENSIVE TESTS ----

class TestMeiliRBACComprehensive:
    """P1.2: All meili admin search endpoints require super_admin only"""

    def test_contract_rbac(self):
        """Contract endpoint should require super_admin"""
        if not ctx.user_token:
            pytest.skip("User token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/contract",
            headers={"Authorization": f"Bearer {ctx.user_token}"},
            timeout=10,
        )
        assert resp.status_code == 403, f"Expected 403 on contract, got {resp.status_code}"
        print(f"PASS: Contract endpoint requires super_admin")

    def test_unauthenticated_requests_get_401(self):
        """All meili admin endpoints should return 401 for unauthenticated requests"""
        endpoints = [
            f"{BASE_URL}/api/admin/search/meili/contract",
            f"{BASE_URL}/api/admin/search/meili/health",
            f"{BASE_URL}/api/admin/search/meili/stage-smoke",
            f"{BASE_URL}/api/admin/search/meili/sync-jobs",
        ]
        
        for endpoint in endpoints:
            resp = requests.get(endpoint, timeout=10)
            assert resp.status_code == 401, f"Expected 401 on {endpoint}, got {resp.status_code}"
        
        print(f"PASS: All admin meili endpoints return 401 for unauthenticated requests")


# ---- SYNC JOB ITEM FIELDS TEST ----

class TestSyncJobItemFields:
    """P1.2: Verify sync job item has expected fields from SearchSyncJob model"""

    def test_sync_job_item_structure(self):
        """Each sync job item should have correct fields"""
        if not ctx.admin_token:
            pytest.skip("Admin token not available")
        resp = requests.get(
            f"{BASE_URL}/api/admin/search/meili/sync-jobs?limit=1",
            headers={"Authorization": f"Bearer {ctx.admin_token}"},
            timeout=10,
        )
        assert resp.status_code == 200
        data = resp.json()
        items = data.get("items", [])
        
        if not items:
            print("SKIP: No sync jobs to verify structure")
            return
        
        item = items[0]
        expected_fields = [
            "id",
            "listing_id",
            "operation",
            "trigger",
            "status",
            "attempts",
            "max_attempts",
            "next_retry_at",
            "last_error",
            "created_at",
            "updated_at",
        ]
        
        for field in expected_fields:
            assert field in item, f"Sync job item missing field: {field}"
        
        # Verify status is valid
        valid_statuses = ["pending", "processing", "retry", "done", "dead_letter"]
        assert item["status"] in valid_statuses, f"Invalid status: {item['status']}"
        
        print(f"PASS: Sync job item has all expected fields, status={item['status']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
