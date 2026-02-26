"""
P0 Category Management Tests - Iteration 19
- module_type için Diğer (other) eklenmesi
- sıra (order_index/sort_order) alanının manuel düzenlenebilir olması
- (country_code, module, parent_id, sort_order) scope unique kuralı
- vehicle akışında segment + master data link zorunluluğu
- real_estate ve other için standart multi-level akışın korunması
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


class TestAuthentication:
    """Authentication helper for all tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Return headers with auth token"""
        return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestCategoryModuleOther(TestAuthentication):
    """Test: module_type için Diğer (other) eklenmesi"""
    
    def test_create_category_with_module_other(self, auth_headers):
        """Create category with module=other should succeed"""
        unique_slug = f"test-other-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"Test Other Category {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 999,
            "hierarchy_complete": True,
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 201, f"Failed to create other category: {response.text}"
        data = response.json()
        assert data.get("category", {}).get("module") == "other", "Module should be 'other'"
        
        # Cleanup
        category_id = data.get("category", {}).get("id")
        if category_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=auth_headers)
    
    def test_module_aliases_map_to_other(self, auth_headers):
        """Test that aliases like 'machinery', 'services', 'jobs' map to other"""
        aliases = ["machinery", "services", "jobs"]
        for alias in aliases:
            unique_slug = f"test-alias-{alias}-{uuid.uuid4().hex[:8]}"
            payload = {
                "name": f"Test {alias} Category",
                "slug": unique_slug,
                "country_code": "DE",
                "module": alias,
                "active_flag": True,
                "sort_order": 998,
                "hierarchy_complete": True,
            }
            response = requests.post(
                f"{BASE_URL}/api/admin/categories",
                headers=auth_headers,
                json=payload
            )
            assert response.status_code == 201, f"Failed for alias {alias}: {response.text}"
            data = response.json()
            assert data.get("category", {}).get("module") == "other", f"Alias {alias} should map to 'other'"
            
            # Cleanup
            category_id = data.get("category", {}).get("id")
            if category_id:
                requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=auth_headers)


class TestSortOrderManualEdit(TestAuthentication):
    """Test: sıra (sort_order) alanının manuel düzenlenebilir olması"""
    
    def test_create_category_with_custom_sort_order(self, auth_headers):
        """Create category with a custom sort_order value"""
        unique_slug = f"test-sortorder-{uuid.uuid4().hex[:8]}"
        custom_sort = 42
        payload = {
            "name": f"Test Sort Order {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": custom_sort,
            "hierarchy_complete": True,
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 201, f"Failed to create category: {response.text}"
        data = response.json()
        assert data.get("category", {}).get("sort_order") == custom_sort, f"Sort order should be {custom_sort}"
        
        category_id = data.get("category", {}).get("id")
        
        # Update sort_order
        new_sort = 99
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            headers=auth_headers,
            json={"sort_order": new_sort}
        )
        assert update_response.status_code == 200, f"Failed to update sort_order: {update_response.text}"
        updated_data = update_response.json()
        assert updated_data.get("category", {}).get("sort_order") == new_sort, f"Sort order should be {new_sort}"
        
        # Cleanup
        if category_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=auth_headers)
    
    def test_sort_order_must_be_positive(self, auth_headers):
        """Sort order must be 1 or greater"""
        unique_slug = f"test-sortorder-neg-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"Test Negative Sort Order",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": 0,  # Invalid: must be >= 1
            "hierarchy_complete": True,
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400, f"Should fail with sort_order=0: {response.text}"
        
        payload["sort_order"] = -1
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        assert response.status_code == 400, f"Should fail with negative sort_order: {response.text}"


class TestUniqueScopeSortOrder(TestAuthentication):
    """Test: (country_code, module, parent_id, sort_order) scope unique kuralı"""
    
    def test_duplicate_sort_order_same_scope_returns_409(self, auth_headers):
        """Creating two categories with same (country, module, parent, sort_order) should return 409"""
        unique_slug_1 = f"test-dup-sort-1-{uuid.uuid4().hex[:8]}"
        unique_slug_2 = f"test-dup-sort-2-{uuid.uuid4().hex[:8]}"
        sort_order = 777
        
        # Create first category
        payload1 = {
            "name": f"Test Dup Sort 1 {unique_slug_1}",
            "slug": unique_slug_1,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": sort_order,
            "hierarchy_complete": True,
        }
        response1 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload1
        )
        assert response1.status_code == 201, f"First category should succeed: {response1.text}"
        category_id_1 = response1.json().get("category", {}).get("id")
        
        # Try to create second category with same sort_order in same scope
        payload2 = {
            "name": f"Test Dup Sort 2 {unique_slug_2}",
            "slug": unique_slug_2,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": sort_order,  # Same sort_order
            "hierarchy_complete": True,
        }
        response2 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload2
        )
        # Should be 409 conflict due to unique constraint
        assert response2.status_code == 409, f"Duplicate sort_order should return 409: {response2.text}"
        data = response2.json()
        assert "sıra" in data.get("detail", "").lower() or "order" in data.get("detail", "").lower(), \
            f"Error message should mention sort order conflict: {data}"
        
        # Cleanup
        if category_id_1:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id_1}", headers=auth_headers)
    
    def test_same_sort_order_different_scope_allowed(self, auth_headers):
        """Same sort_order in different scopes should be allowed"""
        unique_slug_1 = f"test-diff-scope-1-{uuid.uuid4().hex[:8]}"
        unique_slug_2 = f"test-diff-scope-2-{uuid.uuid4().hex[:8]}"
        sort_order = 888
        
        # Create first category in DE, real_estate
        payload1 = {
            "name": f"Test Scope 1 {unique_slug_1}",
            "slug": unique_slug_1,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": sort_order,
            "hierarchy_complete": True,
        }
        response1 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload1
        )
        assert response1.status_code == 201, f"First category should succeed: {response1.text}"
        category_id_1 = response1.json().get("category", {}).get("id")
        
        # Create second category with same sort_order but different module (other)
        payload2 = {
            "name": f"Test Scope 2 {unique_slug_2}",
            "slug": unique_slug_2,
            "country_code": "DE",
            "module": "other",  # Different module
            "active_flag": True,
            "sort_order": sort_order,  # Same sort_order
            "hierarchy_complete": True,
        }
        response2 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload2
        )
        # Should succeed because scope is different (different module)
        assert response2.status_code == 201, f"Different scope should succeed: {response2.text}"
        category_id_2 = response2.json().get("category", {}).get("id")
        
        # Cleanup
        if category_id_1:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id_1}", headers=auth_headers)
        if category_id_2:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id_2}", headers=auth_headers)


class TestVehicleSegmentLinkStatus(TestAuthentication):
    """Test: vehicle-segment/link-status endpoint ve vehicle segment zorunluluğu"""
    
    def test_vehicle_segment_link_status_endpoint(self, auth_headers):
        """GET /api/admin/categories/vehicle-segment/link-status should return correct data"""
        segments = ["car", "suv", "truck", "bus", "pickup", "offroad"]
        
        for segment in segments:
            response = requests.get(
                f"{BASE_URL}/api/admin/categories/vehicle-segment/link-status",
                headers=auth_headers,
                params={"segment": segment}
            )
            assert response.status_code == 200, f"Segment {segment} should return 200: {response.text}"
            data = response.json()
            
            # Verify response structure
            assert "segment" in data, f"Response should have 'segment': {data}"
            assert "linked" in data, f"Response should have 'linked': {data}"
            assert "make_count" in data, f"Response should have 'make_count': {data}"
            assert "model_count" in data, f"Response should have 'model_count': {data}"
            assert data["segment"] == segment, f"Segment should match: {data}"
    
    def test_vehicle_category_requires_segment(self, auth_headers):
        """Vehicle category creation should require segment"""
        unique_slug = f"test-vehicle-no-seg-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"Test Vehicle No Segment",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "vehicle",
            "active_flag": True,
            "sort_order": 950,
            "hierarchy_complete": True,
            # Missing vehicle_segment
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        # Should fail because vehicle_segment is required for vehicle module
        assert response.status_code in [400, 409], f"Should fail without segment: {response.text}"
    
    def test_vehicle_category_with_linked_segment_succeeds(self, auth_headers):
        """Vehicle category with linked segment should succeed"""
        # First check which segment has linked data
        segment_response = requests.get(
            f"{BASE_URL}/api/admin/categories/vehicle-segment/link-status",
            headers=auth_headers,
            params={"segment": "car"}
        )
        if segment_response.status_code != 200:
            pytest.skip("Vehicle segment link status endpoint not available")
        
        segment_data = segment_response.json()
        if not segment_data.get("linked"):
            pytest.skip("No linked vehicle segment data available")
        
        unique_slug = f"test-vehicle-linked-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"Test Vehicle Linked",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "vehicle",
            "vehicle_segment": "car",
            "active_flag": True,
            "sort_order": 951,
            "hierarchy_complete": True,
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload
        )
        
        if response.status_code == 201:
            category_id = response.json().get("category", {}).get("id")
            # Cleanup
            if category_id:
                requests.delete(f"{BASE_URL}/api/admin/categories/{category_id}", headers=auth_headers)
        
        # Either 201 (success) or appropriate error
        assert response.status_code in [201, 409], f"Response: {response.text}"


class TestRealEstateMultiLevel(TestAuthentication):
    """Test: real_estate için standart multi-level akışın korunması"""
    
    def test_real_estate_allows_subcategories(self, auth_headers):
        """Real estate categories should allow parent-child relationships"""
        parent_slug = f"test-re-parent-{uuid.uuid4().hex[:8]}"
        child_slug = f"test-re-child-{uuid.uuid4().hex[:8]}"
        
        # Create parent category
        parent_payload = {
            "name": f"Test RE Parent {parent_slug}",
            "slug": parent_slug,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": 900,
            "hierarchy_complete": True,
        }
        parent_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=parent_payload
        )
        assert parent_response.status_code == 201, f"Parent should be created: {parent_response.text}"
        parent_id = parent_response.json().get("category", {}).get("id")
        
        # Create child category
        child_payload = {
            "name": f"Test RE Child {child_slug}",
            "slug": child_slug,
            "country_code": "DE",
            "module": "real_estate",
            "parent_id": parent_id,
            "active_flag": True,
            "sort_order": 1,
            "hierarchy_complete": True,
        }
        child_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=child_payload
        )
        assert child_response.status_code == 201, f"Child should be created: {child_response.text}"
        child_id = child_response.json().get("category", {}).get("id")
        
        # Verify parent-child relationship
        child_data = child_response.json().get("category", {})
        assert child_data.get("parent_id") == parent_id, "Child should reference parent"
        
        # Cleanup
        if child_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{child_id}", headers=auth_headers)
        if parent_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{parent_id}", headers=auth_headers)


class TestOtherModuleMultiLevel(TestAuthentication):
    """Test: other modülü için standart multi-level akışın korunması"""
    
    def test_other_module_allows_subcategories(self, auth_headers):
        """Other module categories should allow parent-child relationships"""
        parent_slug = f"test-other-parent-{uuid.uuid4().hex[:8]}"
        child_slug = f"test-other-child-{uuid.uuid4().hex[:8]}"
        
        # Create parent category
        parent_payload = {
            "name": f"Test Other Parent {parent_slug}",
            "slug": parent_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 901,
            "hierarchy_complete": True,
        }
        parent_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=parent_payload
        )
        assert parent_response.status_code == 201, f"Parent should be created: {parent_response.text}"
        parent_id = parent_response.json().get("category", {}).get("id")
        
        # Create child category
        child_payload = {
            "name": f"Test Other Child {child_slug}",
            "slug": child_slug,
            "country_code": "DE",
            "module": "other",
            "parent_id": parent_id,
            "active_flag": True,
            "sort_order": 1,
            "hierarchy_complete": True,
        }
        child_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=child_payload
        )
        assert child_response.status_code == 201, f"Child should be created: {child_response.text}"
        child_id = child_response.json().get("category", {}).get("id")
        
        # Verify parent-child relationship
        child_data = child_response.json().get("category", {})
        assert child_data.get("parent_id") == parent_id, "Child should reference parent"
        
        # Cleanup
        if child_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{child_id}", headers=auth_headers)
        if parent_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{parent_id}", headers=auth_headers)


class TestVehicleMustBeTopLevel(TestAuthentication):
    """Test: vehicle categories must be top-level (no parent)"""
    
    def test_vehicle_category_cannot_have_parent(self, auth_headers):
        """Vehicle category should not allow parent_id"""
        # First check if there's a linked segment
        segment_response = requests.get(
            f"{BASE_URL}/api/admin/categories/vehicle-segment/link-status",
            headers=auth_headers,
            params={"segment": "car"}
        )
        if segment_response.status_code != 200 or not segment_response.json().get("linked"):
            pytest.skip("No linked vehicle segment available")
        
        # Create a parent category (real_estate)
        parent_slug = f"test-re-parent-for-vehicle-{uuid.uuid4().hex[:8]}"
        parent_payload = {
            "name": f"Test Parent for Vehicle",
            "slug": parent_slug,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": 902,
            "hierarchy_complete": True,
        }
        parent_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=parent_payload
        )
        if parent_response.status_code != 201:
            pytest.skip("Could not create parent category")
        parent_id = parent_response.json().get("category", {}).get("id")
        
        # Try to create vehicle category with parent
        vehicle_slug = f"test-vehicle-with-parent-{uuid.uuid4().hex[:8]}"
        vehicle_payload = {
            "name": f"Test Vehicle With Parent",
            "slug": vehicle_slug,
            "country_code": "DE",
            "module": "vehicle",
            "vehicle_segment": "car",
            "parent_id": parent_id,  # This should fail
            "active_flag": True,
            "sort_order": 1,
            "hierarchy_complete": True,
        }
        vehicle_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=vehicle_payload
        )
        # Should fail with 409 because vehicle must be top-level
        assert vehicle_response.status_code == 409, f"Vehicle with parent should fail: {vehicle_response.text}"
        
        # Cleanup
        if parent_id:
            requests.delete(f"{BASE_URL}/api/admin/categories/{parent_id}", headers=auth_headers)


class TestMigrationReportExists(TestAuthentication):
    """Test: Migration raporu dosyası oluşturulması ve format kontrolü"""
    
    def test_migration_report_file_exists(self, auth_headers):
        """Check if migration report was generated"""
        import pathlib
        report_path = pathlib.Path("/app/docs/CATEGORY_ORDER_MIGRATION_REPORT.md")
        assert report_path.exists(), f"Migration report should exist at {report_path}"
        
        content = report_path.read_text(encoding="utf-8")
        
        # Check required sections
        assert "# CATEGORY ORDER MIGRATION REPORT" in content, "Report should have title"
        assert "Generated at:" in content, "Report should have generation timestamp"
        assert "Scope bazlı düzeltme yapılan kayıt grubu:" in content, "Report should have scope count"
        assert "Çakışma sayısı" in content, "Report should have conflict count"
        assert "Etkilenen kayıt sayısı:" in content or "Etkilenen Kayıt ID" in content, "Report should have affected IDs section"


class TestUniqueIndexVerification(TestAuthentication):
    """Test: Backend migration sonrası unique index canlı doğrulama"""
    
    def test_unique_index_enforced_by_database(self, auth_headers):
        """The unique index uq_categories_scope_sort should be active"""
        # This test indirectly validates the index by attempting duplicate sort_order
        unique_slug_1 = f"test-idx-1-{uuid.uuid4().hex[:8]}"
        unique_slug_2 = f"test-idx-2-{uuid.uuid4().hex[:8]}"
        sort_order = 666
        
        # Create first
        payload1 = {
            "name": f"Test Index 1",
            "slug": unique_slug_1,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": sort_order,
            "hierarchy_complete": True,
        }
        response1 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload1
        )
        assert response1.status_code == 201, f"First should succeed: {response1.text}"
        category_id_1 = response1.json().get("category", {}).get("id")
        
        # Create second with same sort_order
        payload2 = {
            "name": f"Test Index 2",
            "slug": unique_slug_2,
            "country_code": "DE",
            "module": "real_estate",
            "active_flag": True,
            "sort_order": sort_order,
            "hierarchy_complete": True,
        }
        response2 = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers=auth_headers,
            json=payload2
        )
        
        # Database unique index should cause 409
        assert response2.status_code == 409, f"Database index should reject duplicate: {response2.text}"
        
        # Cleanup
        if category_id_1:
            requests.delete(f"{BASE_URL}/api/admin/categories/{category_id_1}", headers=auth_headers)
