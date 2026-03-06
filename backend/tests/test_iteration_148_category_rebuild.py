"""
Iteration 148: Category Rebuild and Layout Revision Hard Delete Verification Tests

Tests for:
1. Passive/archive category-bound layout revisions hard deleted (expected: 21)
2. Category active counts per country: real_estate=3, vehicle=9, other=99
3. Category root/child hierarchy (other module has 8 root + children = 99 total)
4. Category translations in TR/DE/FR
5. API endpoints: /api/categories/tree for each module
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001').rstrip('/')


class TestCategoryRebuildResults:
    """Verify the category rebuild result report matches expectations"""
    
    def test_hard_deleted_layout_revisions_count(self):
        """Verify 21 layout revisions were hard deleted"""
        report_path = '/app/test_reports/category_rebuild_result.json'
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        assert report.get('hard_deleted_layout_revisions') == 21, \
            f"Expected 21 hard deleted revisions, got {report.get('hard_deleted_layout_revisions')}"
        print(f"PASS: 21 layout revisions hard deleted as expected")
    
    def test_module_mapping_correct(self):
        """Verify module mapping from German to internal names"""
        report_path = '/app/test_reports/category_rebuild_result.json'
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        mapping = report.get('module_mapping', {})
        assert mapping.get('immobilien') == 'real_estate', "Immobilien -> real_estate mapping incorrect"
        assert mapping.get('fahrzeuge') == 'vehicle', "Fahrzeuge -> vehicle mapping incorrect"
        assert mapping.get('diger') == 'other', "Diger -> other mapping incorrect"
        print(f"PASS: Module mapping correct: {mapping}")


class TestCategoryActiveCountsDE:
    """Verify category active counts for DE country"""
    
    def test_de_real_estate_count(self):
        """DE real_estate should have 3 active categories at L1 depth"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=real_estate&depth=L1")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        items = data.get('items', [])
        assert len(items) == 3, f"Expected 3 real_estate categories, got {len(items)}"
        print(f"PASS: DE real_estate has 3 categories: {[i.get('name') for i in items]}")
    
    def test_de_vehicle_count(self):
        """DE vehicle should have 9 active categories at L1 depth"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=vehicle&depth=L1")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        items = data.get('items', [])
        assert len(items) == 9, f"Expected 9 vehicle categories, got {len(items)}"
        print(f"PASS: DE vehicle has 9 categories: {[i.get('name') for i in items]}")
    
    def test_de_other_total_count(self):
        """DE other should have 99 total active categories (8 root + 91 children)"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=other&depth=all")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        items = data.get('items', [])
        
        # Count all categories including children
        def count_all(items_list):
            total = len(items_list)
            for item in items_list:
                children = item.get('children', [])
                total += count_all(children)
            return total
        
        total_count = count_all(items)
        assert total_count == 99, f"Expected 99 total other categories, got {total_count}"
        assert len(items) == 8, f"Expected 8 root other categories, got {len(items)}"
        print(f"PASS: DE other has 8 root categories and {total_count} total (including children)")


class TestCategoryActiveCountsTR:
    """Verify category active counts for TR country"""
    
    def test_tr_real_estate_count(self):
        """TR real_estate should have 3 active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=TR&module=real_estate&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        assert len(items) == 3, f"Expected 3, got {len(items)}"
        print(f"PASS: TR real_estate has 3 categories")
    
    def test_tr_vehicle_count(self):
        """TR vehicle should have 9 active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=TR&module=vehicle&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        assert len(items) == 9, f"Expected 9, got {len(items)}"
        print(f"PASS: TR vehicle has 9 categories")
    
    def test_tr_other_total_count(self):
        """TR other should have 99 total active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=TR&module=other&depth=all")
        assert response.status_code == 200
        items = response.json().get('items', [])
        
        def count_all(items_list):
            total = len(items_list)
            for item in items_list:
                total += count_all(item.get('children', []))
            return total
        
        assert count_all(items) == 99, f"Expected 99 total"
        print(f"PASS: TR other has 99 total categories")


class TestCategoryActiveCountsFR:
    """Verify category active counts for FR country"""
    
    def test_fr_real_estate_count(self):
        """FR real_estate should have 3 active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=FR&module=real_estate&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        assert len(items) == 3, f"Expected 3, got {len(items)}"
        print(f"PASS: FR real_estate has 3 categories")
    
    def test_fr_vehicle_count(self):
        """FR vehicle should have 9 active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=FR&module=vehicle&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        assert len(items) == 9, f"Expected 9, got {len(items)}"
        print(f"PASS: FR vehicle has 9 categories")
    
    def test_fr_other_total_count(self):
        """FR other should have 99 total active categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=FR&module=other&depth=all")
        assert response.status_code == 200
        items = response.json().get('items', [])
        
        def count_all(items_list):
            total = len(items_list)
            for item in items_list:
                total += count_all(item.get('children', []))
            return total
        
        assert count_all(items) == 99
        print(f"PASS: FR other has 99 total categories")


class TestCategoryTranslations:
    """Verify category translations exist in TR/DE/FR"""
    
    def test_translations_have_all_languages(self):
        """Each category should have translations in tr, de, fr"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=real_estate&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        
        for item in items:
            translations = item.get('translations', [])
            langs = sorted([t.get('language') for t in translations])
            assert 'de' in langs, f"Missing DE translation for {item.get('name')}"
            assert 'fr' in langs, f"Missing FR translation for {item.get('name')}"
            assert 'tr' in langs, f"Missing TR translation for {item.get('name')}"
            
            # Also check title_i18n
            title_i18n = item.get('title_i18n', {})
            assert 'de' in title_i18n, f"Missing DE in title_i18n for {item.get('name')}"
            assert 'fr' in title_i18n, f"Missing FR in title_i18n for {item.get('name')}"
            assert 'tr' in title_i18n, f"Missing TR in title_i18n for {item.get('name')}"
        
        print(f"PASS: All {len(items)} real_estate categories have TR/DE/FR translations")
    
    def test_vehicle_translations(self):
        """Vehicle categories should have TR/DE/FR translations"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=vehicle&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        
        for item in items:
            title_i18n = item.get('title_i18n', {})
            assert all(k in title_i18n for k in ['de', 'fr', 'tr']), \
                f"Missing language in title_i18n for {item.get('name')}"
        
        print(f"PASS: All {len(items)} vehicle categories have TR/DE/FR title_i18n")


class TestCategoryHierarchy:
    """Verify category root/child hierarchy"""
    
    def test_other_module_has_8_roots(self):
        """Other module should have 8 root categories"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=other&depth=L1")
        assert response.status_code == 200
        items = response.json().get('items', [])
        assert len(items) == 8, f"Expected 8 root categories, got {len(items)}"
        
        root_names = [i.get('name') for i in items]
        print(f"PASS: Other module has 8 root categories: {root_names}")
    
    def test_other_roots_have_children(self):
        """Other module root categories should have children totaling 91"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=other&depth=all")
        assert response.status_code == 200
        items = response.json().get('items', [])
        
        total_children = sum(len(item.get('children', [])) for item in items)
        assert total_children == 91, f"Expected 91 children, got {total_children}"
        
        print(f"PASS: 8 root categories have {total_children} direct children (99 total)")


class TestCategoryTreeAPIEndpoints:
    """Test the /api/categories/tree endpoints for each module"""
    
    def test_api_tree_real_estate_endpoint(self):
        """GET /api/categories/tree?country=DE&module=real_estate&depth=L1"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=real_estate&depth=L1")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        assert 'meta' in data
        meta = data.get('meta', {})
        assert meta.get('country') == 'DE'
        assert meta.get('module') == 'real_estate'
        print(f"PASS: /api/categories/tree for real_estate returns correct structure")
    
    def test_api_tree_vehicle_endpoint(self):
        """GET /api/categories/tree?country=DE&module=vehicle&depth=L1"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=vehicle&depth=L1")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        meta = data.get('meta', {})
        assert meta.get('module') == 'vehicle'
        print(f"PASS: /api/categories/tree for vehicle returns correct structure")
    
    def test_api_tree_other_endpoint(self):
        """GET /api/categories/tree?country=DE&module=other&depth=L1"""
        response = requests.get(f"{BASE_URL}/api/categories/tree?country=DE&module=other&depth=L1")
        assert response.status_code == 200
        data = response.json()
        assert 'items' in data
        meta = data.get('meta', {})
        assert meta.get('module') == 'other'
        print(f"PASS: /api/categories/tree for other returns correct structure")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
