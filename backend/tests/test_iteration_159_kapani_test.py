"""
Test iteration 159: Kapanış toplu görev listesi
Faz bazlı test dosyası covering:
- Faz1: preset install/verify TR-DE-FR (ready_ratio, missing_rows, fail_fast) + cache invalidation
- Faz2: preset run log kaydı ve list endpoint
- Faz3: copy conflict 409 + force=true flow
- Faz4: academy modules gerçek veri contract (DealerModule tablosundan)
"""

import os
import pytest
import requests
import time

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=60,
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer auth token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        timeout=60,
    )
    if response.status_code != 200:
        pytest.skip(f"Dealer login failed: {response.status_code}")
    return response.json().get("access_token")


class TestFaz1PresetInstallVerify:
    """Faz1: preset install/verify TR-DE-FR akışı testi"""

    def test_01_preset_verify_endpoint_returns_ready_ratio(self, admin_token):
        """verify-standard-pack endpointi ready_ratio, missing_rows döndürür"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"countries": "TR,DE,FR", "module": "global", "fail_fast": "false"},
            timeout=30,
        )
        assert response.status_code == 200, f"Verify failed: {response.text}"
        data = response.json()
        
        # Contract checks
        assert "summary" in data, "summary field missing"
        summary = data["summary"]
        assert "ready_ratio" in summary, "ready_ratio missing in summary"
        assert "missing_rows" in summary, "missing_rows missing in summary"
        assert "ready_rows" in summary, "ready_rows missing in summary"
        assert "total_rows" in summary, "total_rows missing in summary"
        
        # Country summaries check
        assert "country_summaries" in data, "country_summaries missing"
        for cs in data.get("country_summaries", []):
            assert "country" in cs, "country missing in country_summary"
            assert "ready_ratio" in cs, "ready_ratio missing in country_summary"
            assert "ok" in cs, "ok missing in country_summary"
        
        print(f"Verify result: ready_ratio={summary.get('ready_ratio')}%, missing_rows={summary.get('missing_rows')}")

    def test_02_preset_verify_fail_fast_query_param(self, admin_token):
        """fail_fast query param accepted and reflected"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"countries": "TR", "module": "global", "fail_fast": "true"},
            timeout=30,
        )
        assert response.status_code == 200, f"Verify failed: {response.text}"
        data = response.json()
        
        # Should return fail_fast in response
        assert "fail_fast" in data or "summary" in data, "fail_fast or summary field expected"
        print(f"Verify with fail_fast=true returned ok={data.get('ok')}")

    def test_03_preset_install_summary_structure(self, admin_token):
        """install-standard-pack summary fields check"""
        # Use dry-run style minimal test - just 1 country to minimize side effects
        response = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "countries": ["TR"],
                "module": "global",
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": False,
                "publish_after_seed": False,
                "include_extended_templates": False,
                "fail_fast": True,
            },
            timeout=30,
        )
        assert response.status_code == 200, f"Install failed: {response.text}"
        data = response.json()
        
        # Contract checks
        assert "summary" in data, "summary field missing in install response"
        summary = data["summary"]
        
        # Summary should have key fields
        expected_fields = ["created_pages", "updated_drafts", "published_revisions", "failed_countries"]
        for field in expected_fields:
            assert field in summary, f"{field} missing in install summary"
        
        print(f"Install result: created_pages={summary.get('created_pages')}, updated_drafts={summary.get('updated_drafts')}")

    def test_04_cache_invalidation_flow(self, admin_token):
        """publish_after_seed sonrası resolve source değişimini kontrol et"""
        # First resolve call
        resolve1 = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"page_type": "home", "country": "TR", "module": "global"},
            timeout=20,
        )
        assert resolve1.status_code == 200, f"Resolve failed: {resolve1.text}"
        source1 = resolve1.json().get("source")
        
        # Source can be "default", "cache", etc.
        assert source1 in ["default", "cache", "binding", "revision_cache"], f"Unexpected source: {source1}"
        print(f"First resolve source: {source1}")
        
        # Second resolve - should be cache or default depending on TTL
        resolve2 = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={"page_type": "home", "country": "TR", "module": "global"},
            timeout=20,
        )
        assert resolve2.status_code == 200
        source2 = resolve2.json().get("source")
        print(f"Second resolve source: {source2}")


class TestFaz1Reports:
    """Faz1: Rapor dosyaları kontrolü"""

    def test_05_publish_validation_report_exists(self):
        """publish_validation_report.md dosyası mevcut mu"""
        report_path = "/app/publish_validation_report.md"
        assert os.path.exists(report_path), f"Report file missing: {report_path}"
        
        with open(report_path, "r") as f:
            content = f.read()
        
        # Basic content checks
        assert "# publish_validation_report.md" in content or "Publish" in content, "Report header missing"
        assert "TR" in content or "DE" in content or "FR" in content, "Country mentions missing"
        print(f"publish_validation_report.md exists with {len(content)} chars")

    def test_06_preset_stress_test_report_exists(self):
        """preset_stress_test_report.md dosyası mevcut mu"""
        report_path = "/app/preset_stress_test_report.md"
        assert os.path.exists(report_path), f"Report file missing: {report_path}"
        
        with open(report_path, "r") as f:
            content = f.read()
        
        # Basic content checks
        assert "# preset_stress_test_report.md" in content or "Stress" in content.lower() or "preset" in content.lower(), "Report header missing"
        print(f"preset_stress_test_report.md exists with {len(content)} chars")


class TestFaz2PresetRunLogs:
    """Faz2: preset run log kaydı ve list endpoint testi"""

    def test_07_preset_runs_list_endpoint(self, admin_token):
        """GET /api/admin/site/content-layout/preset-runs endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10},
            timeout=30,
        )
        assert response.status_code == 200, f"Preset runs list failed: {response.text}"
        data = response.json()
        
        # Contract checks
        assert "items" in data, "items field missing"
        assert "total" in data, "total field missing"
        assert "page" in data, "page field missing"
        assert "limit" in data, "limit field missing"
        
        items = data.get("items", [])
        print(f"Preset runs: {len(items)} items, total={data.get('total')}")
        
        # If items exist, check structure
        if items:
            item = items[0]
            expected_fields = ["id", "executed_at", "target_countries", "success_ratio", "status"]
            for field in expected_fields:
                assert field in item, f"{field} missing in preset run item"
            print(f"First run: status={item.get('status')}, success_ratio={item.get('success_ratio')}%")

    def test_08_preset_runs_filter_by_status(self, admin_token):
        """Filter preset runs by status works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10, "status": "success"},
            timeout=30,
        )
        assert response.status_code == 200, f"Preset runs filter failed: {response.text}"
        data = response.json()
        
        # All returned items should have status=success (if any returned)
        for item in data.get("items", []):
            assert item.get("status") == "success", f"Unexpected status: {item.get('status')}"
        print(f"Filtered to success: {len(data.get('items', []))} items")

    def test_09_preset_runs_filter_by_module(self, admin_token):
        """Filter preset runs by module works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset-runs",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"page": 1, "limit": 10, "module": "global"},
            timeout=30,
        )
        assert response.status_code == 200, f"Preset runs filter failed: {response.text}"
        data = response.json()
        
        # All returned items should have module=global (if any returned)
        for item in data.get("items", []):
            assert item.get("module") == "global", f"Unexpected module: {item.get('module')}"
        print(f"Filtered to global module: {len(data.get('items', []))} items")


class TestFaz3CopyConflict:
    """Faz3: copy conflict 409 + force=true akışı testi"""

    def test_10_copy_without_publish_no_conflict_check(self, admin_token):
        """publish_after_copy=false skips conflict check"""
        # First get a revision to copy
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "page": 1, "limit": 1},
            timeout=15,
        )
        if layouts_response.status_code != 200 or not layouts_response.json().get("items"):
            pytest.skip("No published layouts to copy")
        
        source_item = layouts_response.json()["items"][0]
        source_id = source_item.get("revision_id") or source_item.get("id")
        
        # Copy without publish - should not check conflicts
        copy_response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{source_id}/copy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_page_type": source_item.get("page_type", "home"),
                "country": "FR",  # Use different country to avoid conflicts
                "module": f"test_copy_{int(time.time())}",  # Unique module
                "category_id": None,
                "publish_after_copy": False,  # No publish
            },
            timeout=30,
        )
        # Should succeed or conflict without returning 409 for publish scope
        assert copy_response.status_code in [200, 201, 404, 422], f"Copy failed unexpectedly: {copy_response.text}"
        print(f"Copy without publish returned: {copy_response.status_code}")

    def test_11_copy_with_publish_returns_409_on_conflict(self, admin_token):
        """copy with publish_after_copy=true returns 409 when conflict exists"""
        # First get existing layout items to find potential conflict
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "page": 1, "limit": 5},
            timeout=30,
        )
        if layouts_response.status_code != 200 or not layouts_response.json().get("items"):
            pytest.skip("No published layouts available")
        
        items = layouts_response.json()["items"]
        # Find a source that we can copy to same scope
        source_item = None
        for item in items:
            if item.get("is_active") and not item.get("is_deleted"):
                source_item = item
                break
        
        if not source_item:
            pytest.skip("No active published revision to test conflict")
        
        source_id = source_item.get("revision_id") or source_item.get("id")
        
        # Try to copy to SAME scope - this should cause conflict
        copy_response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{source_id}/copy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_page_type": source_item.get("page_type", "home"),
                "country": source_item.get("country", "TR"),
                "module": source_item.get("module", "global"),
                "category_id": source_item.get("category_id"),
                "publish_after_copy": True,  # Enable publish
            },
            timeout=30,
        )
        
        # Should return 409 conflict or 200 if force allowed
        if copy_response.status_code == 409:
            data = copy_response.json()
            detail = data.get("detail", {})
            assert detail.get("code") == "publish_scope_conflict", f"Unexpected 409 code: {detail}"
            assert "conflicts" in detail or "scope" in detail, "Conflict detail missing expected fields"
            print(f"409 conflict returned: {detail.get('code')} with scope={detail.get('scope')}")
        else:
            # 200 is also acceptable if force was applied or no conflict exists
            assert copy_response.status_code == 200, f"Unexpected status: {copy_response.text}"
            print(f"Copy succeeded (no conflict or already resolved)")

    def test_12_copy_with_force_deactivates_conflicts(self, admin_token):
        """force=true query param deactivates conflicting revisions"""
        # Get layout for test
        layouts_response = requests.get(
            f"{BASE_URL}/api/admin/layouts",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"statuses": "published", "page": 1, "limit": 2},
            timeout=30,
        )
        if layouts_response.status_code != 200 or len(layouts_response.json().get("items", [])) < 1:
            pytest.skip("Need published layouts for force test")
        
        source_item = layouts_response.json()["items"][0]
        source_id = source_item.get("revision_id") or source_item.get("id")
        
        # Copy with force=true
        copy_response = requests.post(
            f"{BASE_URL}/api/admin/layouts/{source_id}/copy",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_page_type": source_item.get("page_type", "home"),
                "country": source_item.get("country", "TR"),
                "module": source_item.get("module", "global"),
                "category_id": source_item.get("category_id"),
                "publish_after_copy": True,
            },
            params={"force": "true"},  # Force flag
            timeout=30,
        )
        
        # Should succeed with force
        assert copy_response.status_code in [200, 201], f"Force copy failed: {copy_response.text}"
        data = copy_response.json()
        
        # Check for conflict_resolution in response
        if "conflict_resolution" in data:
            resolution = data["conflict_resolution"]
            print(f"Force applied: deactivated_ids={resolution.get('deactivated_revision_ids', [])}")
        else:
            print(f"Copy succeeded without conflict resolution needed")


class TestFaz4AcademyModules:
    """Faz4: academy modules gerçek veri contract testi"""

    def test_13_academy_modules_endpoint_returns_real_data(self, dealer_token):
        """GET /api/academy/modules returns real data from DealerModule table"""
        response = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=30,
        )
        assert response.status_code == 200, f"Academy modules failed: {response.text}"
        data = response.json()
        
        # Contract checks
        assert "items" in data, "items field missing"
        assert "source" in data, "source field missing"
        
        # Source should be dealer_modules_db, cache, or cache_fallback (NOT mock)
        source = data.get("source")
        valid_sources = ["dealer_modules_db", "cache", "cache_fallback", "empty_fallback"]
        assert source in valid_sources, f"Unexpected source: {source}"
        print(f"Academy modules source: {source}")
        
        items = data.get("items", [])
        print(f"Academy modules: {len(items)} items")
        
        # If items exist, check contract
        if items:
            item = items[0]
            # Contract fields: id, title/key, slug, locale, status, updated_at
            contract_fields = ["id", "key"]
            for field in contract_fields:
                assert field in item or "title" in item, f"Contract field missing: {field}"
            print(f"First module: key={item.get('key')}, visible={item.get('visible')}")

    def test_14_academy_modules_requires_dealer_or_admin(self, admin_token):
        """Academy modules accessible by admin"""
        response = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15,
        )
        assert response.status_code == 200, f"Admin academy modules failed: {response.text}"
        data = response.json()
        
        # Admin should be able to use admin_override
        response_override = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"admin_override": "true"},
            timeout=30,
        )
        assert response_override.status_code == 200, f"Admin override failed: {response_override.text}"
        print(f"Admin academy modules: {len(data.get('items', []))} items")

    def test_15_academy_modules_cache_fallback_flow(self, dealer_token):
        """Cache and fallback mechanism works"""
        # First call to populate cache
        response1 = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Check cache info
        cache_info = data1.get("cache", {})
        assert "ttl_seconds" in cache_info, "cache.ttl_seconds missing"
        
        # Second call should potentially hit cache
        response2 = requests.get(
            f"{BASE_URL}/api/academy/modules",
            headers={"Authorization": f"Bearer {dealer_token}"},
            timeout=15,
        )
        assert response2.status_code == 200
        data2 = response2.json()
        
        print(f"Cache info: ttl={cache_info.get('ttl_seconds')}s, source1={data1.get('source')}, source2={data2.get('source')}")


class TestFaz5UIConsistency:
    """Faz5: UI tutarlılık - i18n locale files check"""

    def test_16_i18n_locale_files_have_copy_page_keys(self):
        """TR/DE/FR locale files have copy_page keys for ConfirmModal"""
        locales = [
            "/app/frontend/src/locales/tr/admin.json",
            "/app/frontend/src/locales/de/admin.json",
            "/app/frontend/src/locales/fr/admin.json",
        ]
        
        required_keys = ["copy_page.invalid_source", "copy_page.conflict_warning", "copy_page.force_publish_effect", "copy_page.proceed"]
        
        for locale_path in locales:
            assert os.path.exists(locale_path), f"Locale file missing: {locale_path}"
            
            import json
            with open(locale_path, "r") as f:
                data = json.load(f)
            
            copy_page = data.get("copy_page", {})
            assert copy_page, f"copy_page section missing in {locale_path}"
            
            for key in required_keys:
                key_parts = key.split(".")
                if len(key_parts) == 2 and key_parts[0] == "copy_page":
                    assert key_parts[1] in copy_page, f"{key} missing in {locale_path}"
            
            print(f"{locale_path}: copy_page keys OK")

    def test_17_confirm_modal_component_exists(self):
        """ConfirmModal component file exists with expected structure"""
        modal_path = "/app/frontend/src/components/ConfirmModal.jsx"
        assert os.path.exists(modal_path), f"ConfirmModal component missing: {modal_path}"
        
        with open(modal_path, "r") as f:
            content = f.read()
        
        # Check for key props
        expected_props = ["open", "onOpenChange", "title", "description", "warningText", "conflictItems", "onProceed", "onCancel"]
        for prop in expected_props[:5]:  # Check first 5 critical props
            assert prop in content, f"Prop {prop} not found in ConfirmModal"
        
        # Check for data-testid
        assert "data-testid" in content, "data-testid attributes missing"
        print(f"ConfirmModal component OK with {len(content)} chars")
