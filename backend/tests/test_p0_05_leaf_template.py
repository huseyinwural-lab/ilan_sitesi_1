"""
P0-05 Kategori Leaf -> Form Template Final Doğrulama
Tests for negative API responses with fake leaf IDs and E2E matrix verification
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://header-config-1.preview.emergentagent.com')

# Test credentials
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


class TestP005NegativeAPIs:
    """Tests for negative API scenarios with fake/unmapped leaf IDs"""
    
    def test_catalog_schema_with_fake_leaf_returns_404(self):
        """Verify /api/catalog/schema returns 404 for non-existent category"""
        fake_leaf_id = "9853f177-a280-4966-8e91-e01ff9ab5e58"
        response = requests.get(
            f"{BASE_URL}/api/catalog/schema",
            params={"category_id": fake_leaf_id, "country": "DE"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        # Turkish error message expected: "Kategori bulunamadı"
        assert "bulunamadı" in data["detail"].lower() or "not found" in data["detail"].lower()
        print(f"PASS: /api/catalog/schema returns 404 with detail: {data['detail']}")
    
    def test_categories_validate_with_fake_leaf_returns_404(self):
        """Verify /api/categories/validate returns 404 for non-existent category"""
        fake_leaf_id = "9853f177-a280-4966-8e91-e01ff9ab5e58"
        response = requests.get(
            f"{BASE_URL}/api/categories/validate",
            params={"category_id": fake_leaf_id, "country": "DE"}
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        data = response.json()
        assert "detail" in data
        print(f"PASS: /api/categories/validate returns 404 with detail: {data['detail']}")
    
    def test_catalog_schema_with_invalid_uuid_returns_4xx(self):
        """Verify /api/catalog/schema returns 4xx for invalid UUID format"""
        invalid_id = "not-a-valid-uuid"
        response = requests.get(
            f"{BASE_URL}/api/catalog/schema",
            params={"category_id": invalid_id, "country": "DE"}
        )
        # Should return 400 (bad request) or 404 (not found)
        assert response.status_code in [400, 404, 422], f"Expected 4xx, got {response.status_code}"
        print(f"PASS: /api/catalog/schema returns {response.status_code} for invalid UUID")
    
    def test_categories_validate_with_invalid_uuid_returns_4xx(self):
        """Verify /api/categories/validate returns 4xx for invalid UUID format"""
        invalid_id = "fake-non-existent-leaf-id"
        response = requests.get(
            f"{BASE_URL}/api/categories/validate",
            params={"category_id": invalid_id, "country": "DE"}
        )
        # Should return 400 (bad request) or 404 (not found)
        assert response.status_code in [400, 404, 422], f"Expected 4xx, got {response.status_code}"
        print(f"PASS: /api/categories/validate returns {response.status_code} for invalid UUID")


class TestP005InventoryVerification:
    """Tests to verify the inventory report shows all publishable leaves are mapped"""
    
    def test_inventory_report_exists(self):
        """Verify inventory report file exists"""
        report_path = "/app/test_reports/p0_05_leaf_template_inventory.json"
        assert os.path.exists(report_path), f"Inventory report not found at {report_path}"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert "summary" in data, "Inventory report missing 'summary' field"
        print(f"PASS: Inventory report exists with {data['summary']['total_rows']} rows")
    
    def test_inventory_unmapped_publishable_count_is_zero(self):
        """Verify unmapped publishable count is 0"""
        report_path = "/app/test_reports/p0_05_leaf_template_inventory.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        unmapped_count = data["summary"]["unmapped_publishable_count"]
        assert unmapped_count == 0, f"Expected 0 unmapped publishable leaves, got {unmapped_count}"
        print(f"PASS: Unmapped publishable count is {unmapped_count}")
    
    def test_inventory_acceptance_mapping_missing_is_pass(self):
        """Verify acceptance_mapping_missing status is PASS"""
        report_path = "/app/test_reports/p0_05_leaf_template_inventory.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        status = data["summary"]["acceptance_mapping_missing"]
        assert status == "PASS", f"Expected 'PASS', got '{status}'"
        print(f"PASS: acceptance_mapping_missing = {status}")
    
    def test_inventory_countries_coverage(self):
        """Verify DE and FR countries are in the inventory"""
        report_path = "/app/test_reports/p0_05_leaf_template_inventory.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        countries = data.get("countries_targeted", [])
        assert "DE" in countries, "Germany (DE) not in targeted countries"
        assert "FR" in countries, "France (FR) not in targeted countries"
        print(f"PASS: Countries coverage verified: {countries}")


class TestP005E2EMatrixVerification:
    """Tests to verify the E2E matrix report shows all 12 leaves passed"""
    
    def test_e2e_matrix_report_exists(self):
        """Verify E2E matrix report file exists"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        assert os.path.exists(report_path), f"E2E matrix report not found at {report_path}"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        assert "summary" in data, "E2E matrix report missing 'summary' field"
        assert "results" in data, "E2E matrix report missing 'results' field"
        print(f"PASS: E2E matrix report exists with {len(data['results'])} results")
    
    def test_e2e_matrix_12_leaves_tested(self):
        """Verify exactly 12 leaves were tested"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        total = data["summary"]["total"]
        assert total == 12, f"Expected 12 leaves tested, got {total}"
        print(f"PASS: Exactly {total} leaves tested (6 real_estate + 6 vehicle)")
    
    def test_e2e_matrix_all_12_pass(self):
        """Verify all 12 leaves passed the E2E test"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        pass_count = data["summary"]["pass"]
        fail_count = data["summary"]["fail"]
        
        assert pass_count == 12, f"Expected 12 passes, got {pass_count}"
        assert fail_count == 0, f"Expected 0 failures, got {fail_count}"
        print(f"PASS: All 12/12 leaves passed E2E matrix")
    
    def test_e2e_matrix_acceptance_status(self):
        """Verify acceptance_12_of_12 status is PASS"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        status = data["summary"]["acceptance_12_of_12"]
        assert status == "PASS", f"Expected 'PASS', got '{status}'"
        print(f"PASS: acceptance_12_of_12 = {status}")
    
    def test_e2e_matrix_negative_backend_test_pass(self):
        """Verify negative backend test passed"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        status = data["summary"]["negative_backend_test"]
        assert status == "PASS", f"Expected 'PASS', got '{status}'"
        print(f"PASS: negative_backend_test = {status}")
    
    def test_e2e_matrix_all_steps_200_or_expected(self):
        """Verify all steps in each result return 200 or expected status"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        for result in data["results"]:
            slug = result["slug"]
            status = result["status"]
            assert status == "PASS", f"Leaf {slug} failed with status {status}"
            
            steps = result["steps"]
            for step_name, step_data in steps.items():
                step_status = step_data.get("status")
                expected = step_data.get("expected")
                
                if expected:
                    # For validation enforcement, 422 is expected
                    assert step_status == expected, f"Leaf {slug} step {step_name}: expected {expected}, got {step_status}"
                else:
                    # For all other steps, 200 is expected
                    assert step_status == 200, f"Leaf {slug} step {step_name}: expected 200, got {step_status}"
        
        print(f"PASS: All {len(data['results'])} leaves have valid step statuses")
    
    def test_e2e_matrix_6_real_estate_leaves(self):
        """Verify 6 real estate leaves are in the matrix"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        real_estate_count = len(data["selected_real_estate"])
        assert real_estate_count == 6, f"Expected 6 real_estate leaves, got {real_estate_count}"
        print(f"PASS: {real_estate_count} real_estate leaves in matrix")
    
    def test_e2e_matrix_6_vehicle_leaves(self):
        """Verify 6 vehicle leaves are in the matrix"""
        report_path = "/app/test_reports/p0_05_leaf_template_e2e_matrix.json"
        
        with open(report_path, 'r') as f:
            data = json.load(f)
        
        vehicle_count = len(data["selected_vehicle"])
        assert vehicle_count == 6, f"Expected 6 vehicle leaves, got {vehicle_count}"
        print(f"PASS: {vehicle_count} vehicle leaves in matrix")


class TestP005EndpointsAvailability:
    """Tests to verify critical API endpoints are available"""
    
    def test_categories_endpoint_available(self):
        """Verify /api/categories endpoint is available"""
        response = requests.get(f"{BASE_URL}/api/categories", params={"country": "DE"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: /api/categories returns 200")
    
    def test_categories_children_endpoint_available(self):
        """Verify /api/categories/children endpoint is available"""
        response = requests.get(
            f"{BASE_URL}/api/categories/children",
            params={"country": "DE", "module": "vehicle"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list response"
        print(f"PASS: /api/categories/children returns {len(data)} categories")
    
    def test_health_endpoint_available(self):
        """Verify health endpoint is available"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: /api/health returns 200")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
