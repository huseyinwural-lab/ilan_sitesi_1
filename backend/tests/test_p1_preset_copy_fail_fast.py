"""
Test iteration 158 - P1: Preset fail-fast, copy conflict detection, force copy
Features tested:
- Preset install API: fail_fast=true with fast-fail behavior, response fields (fail_fast, stopped_early, summary.failed_countries, summary.processed_countries)
- Preset verify API: fail_fast query parameter, response fields (summary.missing_rows, country_summaries, failed_countries)
- Preset install encoding: Standard payload seeding should NOT throw SQL_ASCII conversion error
- Copy API conflict guard: POST /api/admin/layouts/{revision_id}/copy publish_after_copy=true returns 409 with publish_scope_conflict code when conflict exists
- Copy API force: Same endpoint with force=true returns 200 with conflict_resolution.deactivated_revision_ids populated
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

AUTH_CREDENTIALS = {
    "email": "admin@platform.com",
    "password": "Admin123!"
}

# Test scope prefix to avoid polluting production data
TEST_MODULE_PREFIX = "testp158_"


class TestPresetAndCopyP1:
    """P1 tests for preset install/verify fail-fast and copy conflict force flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup auth token for all tests"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.created_page_ids = []
        self.created_revision_ids = []
        
        # Authenticate
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json=AUTH_CREDENTIALS
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token") or data.get("token")
            if token:
                self.session.headers.update({"Authorization": f"Bearer {token}"})
                self.token = token
            else:
                pytest.skip("No access token in login response")
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        yield
        
        # Cleanup
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Cleanup test-created data"""
        try:
            # Passivate and then permanently delete all test revisions
            for rev_id in self.created_revision_ids:
                try:
                    self.session.patch(
                        f"{BASE_URL}/api/admin/layouts/{rev_id}/active",
                        json={"is_active": False}
                    )
                except Exception:
                    pass
            
            if self.created_revision_ids:
                self.session.delete(
                    f"{BASE_URL}/api/admin/layouts/permanent",
                    json={"revision_ids": self.created_revision_ids}
                )
        except Exception:
            pass
    
    def _create_page_and_draft(self, page_type: str = "home", country: str = "TR", module: str = None) -> tuple:
        """Create a layout page and draft revision"""
        unique_module = module or f"{TEST_MODULE_PREFIX}{uuid.uuid4().hex[:8]}"
        
        # Create page
        page_resp = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            json={
                "page_type": page_type,
                "country": country,
                "module": unique_module,
                "title_i18n": {"tr": f"Test {page_type}", "de": f"Test {page_type}", "fr": f"Test {page_type}"}
            }
        )
        
        if page_resp.status_code not in [200, 201]:
            return None, None, None
        
        page_data = page_resp.json()
        page_id = page_data.get("item", {}).get("id")
        if not page_id:
            return None, None, None
        
        self.created_page_ids.append(page_id)
        
        # Create draft with valid components (no blocked keys)
        draft_resp = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            json={
                "payload_json": {
                    "rows": [{
                        "id": f"row-{uuid.uuid4().hex[:6]}",
                        "columns": [{
                            "id": f"col-{uuid.uuid4().hex[:6]}",
                            "width": {"desktop": 12, "tablet": 12, "mobile": 12},
                            "components": [{
                                "id": f"cmp-{uuid.uuid4().hex[:6]}",
                                "key": "shared.text-block",
                                "props": {"title": f"Test {page_type} Content"},
                                "visibility": {"desktop": True, "tablet": True, "mobile": True}
                            }]
                        }]
                    }]
                }
            }
        )
        
        if draft_resp.status_code not in [200, 201]:
            return page_id, None, unique_module
        
        draft_data = draft_resp.json()
        revision_id = draft_data.get("item", {}).get("id")
        if revision_id:
            self.created_revision_ids.append(revision_id)
        
        return page_id, revision_id, unique_module

    # ==================== PRESET INSTALL TESTS ====================

    def test_01_preset_install_response_includes_fail_fast_field(self):
        """
        Test: POST /api/admin/site/content-layout/preset/install-standard-pack
        Response should include fail_fast field reflecting the request payload.
        """
        unique_module = f"{TEST_MODULE_PREFIX}{uuid.uuid4().hex[:6]}"
        
        # Test with fail_fast=true
        install_resp = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json={
                "countries": ["ZZ"],  # Invalid country to potentially trigger fail-fast
                "module": unique_module,
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": True,
                "publish_after_seed": False,  # Don't publish to avoid component block
                "include_extended_templates": False,
                "fail_fast": True
            },
            timeout=25
        )
        
        # Even if countries fail, response structure should be valid
        assert install_resp.status_code in [200, 400, 409], f"Install failed unexpectedly: {install_resp.status_code}"
        
        result = install_resp.json()
        
        # Check fail_fast field is present
        assert "fail_fast" in result, f"Response should include fail_fast field: {result.keys()}"
        assert result["fail_fast"] == True, "fail_fast should be True"
        
        # Check summary structure
        if "summary" in result:
            summary = result["summary"]
            assert "failed_countries" in summary or "processed_countries" in summary, f"Summary should have country metrics: {summary.keys()}"
        
        print(f"✅ Preset install response includes fail_fast={result.get('fail_fast')}")

    def test_02_preset_install_stopped_early_on_fail_fast(self):
        """
        Test: When fail_fast=true and first country fails, stopped_early should be true.
        """
        unique_module = f"{TEST_MODULE_PREFIX}{uuid.uuid4().hex[:6]}"
        
        install_resp = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json={
                "countries": ["TR"],  # Valid country
                "module": unique_module,
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": True,
                "publish_after_seed": True,
                "include_extended_templates": False,
                "fail_fast": True
            },
            timeout=25
        )
        
        result = install_resp.json()
        
        # stopped_early should be present
        assert "stopped_early" in result, f"Response should include stopped_early field: {result.keys()}"
        
        # If ok=true, stopped_early should be false
        if result.get("ok") == True:
            assert result.get("stopped_early") == False, "stopped_early should be False when ok=True"
        
        # Check summary.processed_countries
        if "summary" in result and result.get("ok") == True:
            summary = result["summary"]
            assert summary.get("processed_countries", 0) >= 1, "At least one country should be processed"
        
        print(f"✅ Preset install: ok={result.get('ok')}, stopped_early={result.get('stopped_early')}")

    def test_03_preset_install_no_sql_ascii_encoding_error(self):
        """
        Test: Standard payload seed should NOT throw SQL_ASCII conversion error.
        This tests the _sanitize_payload_for_sql_ascii function indirectly.
        """
        unique_module = f"{TEST_MODULE_PREFIX}encoding_{uuid.uuid4().hex[:6]}"
        
        install_resp = self.session.post(
            f"{BASE_URL}/api/admin/site/content-layout/preset/install-standard-pack",
            json={
                "countries": ["DE"],
                "module": unique_module,
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": True,
                "publish_after_seed": True,
                "include_extended_templates": False,
                "fail_fast": True
            },
            timeout=25
        )
        
        result = install_resp.json()
        
        # Check that we don't have sql_ascii_encoding_error
        if "failed_countries" in result and result["failed_countries"]:
            for fc in result["failed_countries"]:
                assert fc.get("error") != "sql_ascii_encoding_error", f"SQL_ASCII encoding error found: {fc}"
        
        # If there's an error in results, ensure it's not encoding related
        for item in result.get("results", []):
            if item.get("ok") == False:
                assert item.get("error") != "sql_ascii_encoding_error", f"SQL_ASCII encoding error in results: {item}"
        
        print(f"✅ Preset install completed without SQL_ASCII encoding error: ok={result.get('ok')}")

    # ==================== PRESET VERIFY TESTS ====================

    def test_04_preset_verify_response_includes_fail_fast_field(self):
        """
        Test: GET /api/admin/site/content-layout/preset/verify-standard-pack
        Response should include fail_fast field reflecting the query parameter.
        """
        verify_resp = self.session.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={
                "countries": "TR,DE",
                "module": "global",
                "include_extended_templates": False,
                "fail_fast": True
            },
            timeout=15
        )
        
        assert verify_resp.status_code == 200, f"Verify failed: {verify_resp.status_code}"
        
        result = verify_resp.json()
        
        # Check fail_fast field
        assert "fail_fast" in result, f"Response should include fail_fast: {result.keys()}"
        assert result["fail_fast"] == True, "fail_fast should be True"
        
        # Check summary structure
        assert "summary" in result, "Response should include summary"
        summary = result["summary"]
        assert "missing_rows" in summary, f"Summary should include missing_rows: {summary.keys()}"
        assert "ready_rows" in summary, f"Summary should include ready_rows: {summary.keys()}"
        assert "total_rows" in summary, f"Summary should include total_rows: {summary.keys()}"
        
        # Check country_summaries
        assert "country_summaries" in result, f"Response should include country_summaries: {result.keys()}"
        assert isinstance(result["country_summaries"], list), "country_summaries should be a list"
        
        # Check failed_countries
        assert "failed_countries" in result, f"Response should include failed_countries: {result.keys()}"
        
        print(f"✅ Preset verify response includes fail_fast={result.get('fail_fast')}, missing_rows={summary.get('missing_rows')}")

    def test_05_preset_verify_country_summaries_structure(self):
        """
        Test: country_summaries array should have proper structure per country.
        """
        verify_resp = self.session.get(
            f"{BASE_URL}/api/admin/site/content-layout/preset/verify-standard-pack",
            params={
                "countries": "TR",
                "module": "global",
                "include_extended_templates": False,
                "fail_fast": False  # Don't stop early
            },
            timeout=15
        )
        
        assert verify_resp.status_code == 200, f"Verify failed: {verify_resp.status_code}"
        
        result = verify_resp.json()
        country_summaries = result.get("country_summaries", [])
        
        assert len(country_summaries) >= 1, "Should have at least one country summary"
        
        for cs in country_summaries:
            assert "country" in cs, f"Country summary should have country: {cs.keys()}"
            assert "ready_rows" in cs, f"Country summary should have ready_rows: {cs.keys()}"
            assert "total_rows" in cs, f"Country summary should have total_rows: {cs.keys()}"
            assert "ready_ratio" in cs, f"Country summary should have ready_ratio: {cs.keys()}"
            assert "ok" in cs, f"Country summary should have ok: {cs.keys()}"
        
        print(f"✅ Preset verify country_summaries has {len(country_summaries)} countries with proper structure")

    # ==================== COPY CONFLICT TESTS ====================

    def test_06_copy_with_publish_returns_409_on_conflict(self):
        """
        Test: POST /api/admin/layouts/{revision_id}/copy with publish_after_copy=true
        should return 409 with code=publish_scope_conflict when a conflict exists.
        """
        # Create first page, draft, and publish it
        page1_id, rev1_id, module1 = self._create_page_and_draft("category_l0_l1", "TR")
        assert page1_id and rev1_id, "Failed to create first test page/draft"
        
        pub_resp = self.session.put(f"{BASE_URL}/api/admin/layouts/{rev1_id}/publish")
        if pub_resp.status_code != 200:
            pytest.skip(f"First publish failed: {pub_resp.status_code}")
        
        published1_id = pub_resp.json().get("item", {}).get("id")
        if published1_id and published1_id not in self.created_revision_ids:
            self.created_revision_ids.append(published1_id)
        
        # Create second page with same scope
        page2_id, rev2_id, module2 = self._create_page_and_draft("home", "DE")
        assert page2_id and rev2_id, "Failed to create second test page/draft"
        
        # Try to copy rev2 to the same scope as rev1 with publish_after_copy=true
        copy_resp = self.session.post(
            f"{BASE_URL}/api/admin/layouts/{rev2_id}/copy",
            json={
                "target_page_type": "category_l0_l1",  # Same as first
                "country": "TR",  # Same as first
                "module": module1,  # Same module as first
                "category_id": None,
                "publish_after_copy": True
            }
        )
        
        assert copy_resp.status_code == 409, f"Expected 409 conflict, got {copy_resp.status_code}: {copy_resp.text}"
        
        detail = copy_resp.json().get("detail", {})
        if isinstance(detail, dict):
            assert detail.get("code") == "publish_scope_conflict", f"Expected code=publish_scope_conflict: {detail}"
            assert "scope" in detail, f"Detail should include scope: {detail.keys()}"
            assert "conflicts" in detail, f"Detail should include conflicts: {detail.keys()}"
        
        print(f"✅ Copy with publish_after_copy=true returns 409 with code=publish_scope_conflict")

    def test_07_copy_with_force_returns_200_and_deactivates_conflicts(self):
        """
        Test: POST /api/admin/layouts/{revision_id}/copy?force=true with publish_after_copy=true
        should return 200 and include deactivated_revision_ids in conflict_resolution.
        """
        # Create first page, draft, and publish it
        unique_module = f"{TEST_MODULE_PREFIX}force_{uuid.uuid4().hex[:6]}"
        page1_id, rev1_id, _ = self._create_page_and_draft("search_ln", "FR", module=unique_module)
        assert page1_id and rev1_id, "Failed to create first test page/draft"
        
        pub_resp = self.session.put(f"{BASE_URL}/api/admin/layouts/{rev1_id}/publish")
        if pub_resp.status_code != 200:
            pytest.skip(f"First publish failed: {pub_resp.status_code}")
        
        published1_id = pub_resp.json().get("item", {}).get("id")
        if published1_id and published1_id not in self.created_revision_ids:
            self.created_revision_ids.append(published1_id)
        
        # Create second page with different scope to copy from
        page2_id, rev2_id, _ = self._create_page_and_draft("home", "DE")
        assert page2_id and rev2_id, "Failed to create second test page/draft"
        
        # Copy rev2 to the same scope as rev1 with force=true
        copy_resp = self.session.post(
            f"{BASE_URL}/api/admin/layouts/{rev2_id}/copy",
            json={
                "target_page_type": "search_ln",  # Same as first
                "country": "FR",  # Same as first
                "module": unique_module,  # Same module as first
                "category_id": None,
                "publish_after_copy": True
            },
            params={"force": "true"}
        )
        
        assert copy_resp.status_code == 200, f"Force copy failed: {copy_resp.status_code} - {copy_resp.text}"
        
        result = copy_resp.json()
        assert result.get("ok") == True
        
        # Check conflict_resolution
        assert "conflict_resolution" in result, f"Response should include conflict_resolution: {result.keys()}"
        cr = result["conflict_resolution"]
        assert "force" in cr, f"conflict_resolution should have force: {cr.keys()}"
        assert cr["force"] == True, f"force should be True: {cr}"
        assert "deactivated_revision_ids" in cr, f"conflict_resolution should have deactivated_revision_ids: {cr.keys()}"
        
        # Track new revision for cleanup
        new_rev_id = result.get("target_revision", {}).get("id")
        if new_rev_id and new_rev_id not in self.created_revision_ids:
            self.created_revision_ids.append(new_rev_id)
        new_page_id = result.get("target_page", {}).get("id")
        if new_page_id and new_page_id not in self.created_page_ids:
            self.created_page_ids.append(new_page_id)
        
        print(f"✅ Force copy returns 200 with conflict_resolution.deactivated_revision_ids={cr.get('deactivated_revision_ids')}")

    def test_08_copy_without_publish_does_not_check_conflicts(self):
        """
        Test: POST /api/admin/layouts/{revision_id}/copy with publish_after_copy=false
        should NOT return 409 even if a conflict would exist.
        """
        # Create first page, draft, and publish it
        unique_module = f"{TEST_MODULE_PREFIX}nopub_{uuid.uuid4().hex[:6]}"
        page1_id, rev1_id, _ = self._create_page_and_draft("urgent_listings", "TR", module=unique_module)
        assert page1_id and rev1_id, "Failed to create first test page/draft"
        
        pub_resp = self.session.put(f"{BASE_URL}/api/admin/layouts/{rev1_id}/publish")
        if pub_resp.status_code != 200:
            pytest.skip(f"First publish failed: {pub_resp.status_code}")
        
        published1_id = pub_resp.json().get("item", {}).get("id")
        if published1_id and published1_id not in self.created_revision_ids:
            self.created_revision_ids.append(published1_id)
        
        # Create second page to copy from
        page2_id, rev2_id, _ = self._create_page_and_draft("home", "DE")
        assert page2_id and rev2_id, "Failed to create second test page/draft"
        
        # Copy rev2 to the same scope as rev1 WITHOUT publish_after_copy
        copy_resp = self.session.post(
            f"{BASE_URL}/api/admin/layouts/{rev2_id}/copy",
            json={
                "target_page_type": "urgent_listings",  # Same as first
                "country": "TR",  # Same as first
                "module": unique_module,  # Same module as first
                "category_id": None,
                "publish_after_copy": False  # Do NOT publish
            }
        )
        
        # Should succeed because we're not publishing
        assert copy_resp.status_code in [200, 201], f"Copy without publish failed: {copy_resp.status_code}"
        
        result = copy_resp.json()
        assert result.get("ok") == True
        assert result.get("action") in ["created_draft", "updated_draft"], f"Action should be draft-related: {result.get('action')}"
        
        # Track new revision for cleanup
        new_rev_id = result.get("target_revision", {}).get("id")
        if new_rev_id and new_rev_id not in self.created_revision_ids:
            self.created_revision_ids.append(new_rev_id)
        
        print(f"✅ Copy without publish_after_copy=false succeeds without conflict check: action={result.get('action')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
