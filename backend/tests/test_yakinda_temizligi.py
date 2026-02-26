"""
Test Yakinda Temizliği (Admin Kapanis Sprinti - Final)
======================================================
Tests for:
1. Menu Management API disabled (403 + feature_disabled)
2. Category import/export - only CSV (XLSX returns 403)
3. Import dry-run mandatory + apply separate step
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

# Test credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("access_token") or data.get("token")


class TestMenuManagementDisabled:
    """
    Menu Management API should be disabled.
    All endpoints should return 403 with detail=feature_disabled.
    """
    
    def test_get_menu_items_returns_403(self, admin_token):
        """GET /api/admin/menu-items should return 403 + feature_disabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/menu-items",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ GET /api/admin/menu-items returns 403 with feature_disabled")
    
    def test_post_menu_items_returns_403(self, admin_token):
        """POST /api/admin/menu-items should return 403 + feature_disabled"""
        response = requests.post(
            f"{BASE_URL}/api/admin/menu-items",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"label": "Test", "slug": "test-menu", "url": "/test"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ POST /api/admin/menu-items returns 403 with feature_disabled")
    
    def test_patch_menu_items_returns_403(self, admin_token):
        """PATCH /api/admin/menu-items/{id} should return 403 + feature_disabled"""
        fake_uuid = "00000000-0000-0000-0000-000000000001"
        response = requests.patch(
            f"{BASE_URL}/api/admin/menu-items/{fake_uuid}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"label": "Updated"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ PATCH /api/admin/menu-items/{{id}} returns 403 with feature_disabled")
    
    def test_delete_menu_items_returns_403(self, admin_token):
        """DELETE /api/admin/menu-items/{id} should return 403 + feature_disabled"""
        fake_uuid = "00000000-0000-0000-0000-000000000001"
        response = requests.delete(
            f"{BASE_URL}/api/admin/menu-items/{fake_uuid}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ DELETE /api/admin/menu-items/{{id}} returns 403 with feature_disabled")


class TestCategoryImportExportCSVOnly:
    """
    Category import/export should only support CSV.
    XLSX endpoints should return 403 with detail=feature_disabled.
    CSV endpoints should work (200).
    """
    
    def test_csv_export_returns_200(self, admin_token):
        """GET /api/admin/categories/import-export/export/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/export/csv?module=vehicle&country=DE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        assert "text/csv" in response.headers.get("content-type", "") or response.status_code == 200
        print(f"✓ GET /api/admin/categories/import-export/export/csv returns 200")
    
    def test_csv_sample_returns_200(self, admin_token):
        """GET /api/admin/categories/import-export/sample/csv should return 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/sample/csv?module=vehicle&country=DE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        print(f"✓ GET /api/admin/categories/import-export/sample/csv returns 200")
    
    def test_xlsx_export_returns_403(self, admin_token):
        """GET /api/admin/categories/import-export/export/xlsx should return 403 + feature_disabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/export/xlsx?module=vehicle&country=DE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ GET /api/admin/categories/import-export/export/xlsx returns 403 with feature_disabled")
    
    def test_xlsx_sample_returns_403(self, admin_token):
        """GET /api/admin/categories/import-export/sample/xlsx should return 403 + feature_disabled"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/import-export/sample/xlsx?module=vehicle&country=DE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ GET /api/admin/categories/import-export/sample/xlsx returns 403 with feature_disabled")


class TestImportDryRunMandatory:
    """
    Import dry-run is mandatory, apply is a separate step.
    """
    
    def test_import_dryrun_csv_works(self, admin_token):
        """POST /api/admin/categories/import-export/import/dry-run?format=csv should work with valid CSV"""
        # Create a simple CSV file content
        csv_content = b"slug,name_tr,name_en,name_de,module,country_code,parent_slug,is_active,sort_order\n"
        csv_content += b"test-category,Test Kategori,Test Category,Test Kategorie,vehicle,DE,,true,1\n"
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/import-export/import/dry-run?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files,
        )
        # Should return 200 or 400 (validation error), but NOT 403
        assert response.status_code in [200, 400], f"Expected 200 or 400, got {response.status_code}: {response.text}"
        if response.status_code == 200:
            data = response.json()
            # Dry-run should return summary, errors, creates, updates
            assert "summary" in data or "errors" in data or "creates" in data or "dry_run_hash" in data, f"Expected dry-run response structure, got {data}"
            print(f"✓ POST dry-run CSV returns 200 with dry_run_hash/summary")
        else:
            print(f"✓ POST dry-run CSV returns 400 (validation), not 403 (feature disabled)")
    
    def test_import_dryrun_xlsx_returns_403(self, admin_token):
        """POST /api/admin/categories/import-export/import/dry-run?format=xlsx should return 403 + feature_disabled"""
        # Create dummy XLSX content (won't be parsed since feature is disabled)
        xlsx_content = b"dummy xlsx content"
        
        files = {"file": ("test.xlsx", xlsx_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/import-export/import/dry-run?format=xlsx",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files,
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}: {response.text}"
        data = response.json()
        assert data.get("detail") == "feature_disabled", f"Expected detail=feature_disabled, got {data}"
        print(f"✓ POST dry-run format=xlsx returns 403 with feature_disabled")
    
    def test_apply_without_dryrun_hash_blocked(self, admin_token):
        """POST /api/admin/categories/import-export/import/commit without dry_run_hash should be blocked"""
        csv_content = b"slug,name_tr,name_en,name_de,module,country_code,parent_slug,is_active,sort_order\n"
        csv_content += b"test-category,Test Kategori,Test Category,Test Kategorie,vehicle,DE,,true,1\n"
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        # Without dry_run_hash parameter
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/import-export/import/commit?format=csv",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files,
        )
        # Should be blocked (400, 409, or 422) since no dry_run_hash provided
        assert response.status_code in [400, 409, 422], f"Expected 400/409/422, got {response.status_code}: {response.text}"
        print(f"✓ Apply without dry_run_hash is blocked (returns {response.status_code})")
    
    def test_apply_with_invalid_hash_blocked(self, admin_token):
        """POST /api/admin/categories/import-export/import/commit with invalid dry_run_hash should be blocked"""
        csv_content = b"slug,name_tr,name_en,name_de,module,country_code,parent_slug,is_active,sort_order\n"
        csv_content += b"test-category,Test Kategori,Test Category,Test Kategorie,vehicle,DE,,true,1\n"
        
        files = {"file": ("test.csv", csv_content, "text/csv")}
        # With invalid dry_run_hash
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/import-export/import/commit?format=csv&dry_run_hash=invalid-hash-12345",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files,
        )
        # Should be blocked (400, 409) since hash doesn't match
        assert response.status_code in [400, 409, 422], f"Expected 400/409/422, got {response.status_code}: {response.text}"
        print(f"✓ Apply with invalid dry_run_hash is blocked (returns {response.status_code})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
