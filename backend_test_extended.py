import requests
import sys
import json
from datetime import datetime

class ExtendedAdminAPITester:
    def __init__(self, base_url="https://category-wizard-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        if params:
            url += f"?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                
                self.failures.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint
                })
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.failures.append({
                'test': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def login_admin(self):
        """Login to get token"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_categories_by_module(self):
        """Test categories endpoint with module filter"""
        modules = ['real_estate', 'vehicle', 'machinery', 'services', 'jobs']
        results = {}
        
        for module in modules:
            success, data = self.run_test(
                f"Get Categories ({module})",
                "GET",
                "/categories",
                200,
                params={'module': module}
            )
            if success:
                results[module] = len(data)
                print(f"   Found {len(data)} categories")
                
        return results

    def test_category_tree(self):
        """Test category tree endpoint"""
        success, data = self.run_test(
            "Get Category Tree (real_estate)",
            "GET",
            "/categories/tree",
            200,
            params={'module': 'real_estate'}
        )
        if success:
            print(f"   Tree structure loaded")
        return success

    def test_attributes_by_type(self):
        """Test attributes endpoint with type filter"""
        types = ['text', 'number', 'select', 'boolean']
        results = {}
        
        for attr_type in types:
            success, data = self.run_test(
                f"Get Attributes ({attr_type})",
                "GET", 
                "/attributes",
                200,
                params={'attribute_type': attr_type}
            )
            if success:
                results[attr_type] = len(data)
                print(f"   Found {len(data)} {attr_type} attributes")
                
        return results

    def test_menu_top_items(self):
        """Test top menu items"""
        success, data = self.run_test(
            "Get Top Menu Items",
            "GET",
            "/menu/top-items",
            200
        )
        if success:
            print(f"   Found {len(data)} menu items")
            enabled = [item for item in data if item.get('is_enabled', False)]
            print(f"   {len(enabled)} items enabled")
        return success, data

    def test_home_layout_endpoints(self):
        """Test home layout endpoints for each country"""
        countries = ['DE', 'CH', 'FR', 'AT']
        
        for country in countries:
            success, data = self.run_test(
                f"Get Home Layout ({country})",
                "GET",
                f"/home/layout/{country}",
                200
            )
            if success:
                print(f"   Layout config loaded")

    def test_create_category(self):
        """Test creating a new category"""
        category_data = {
            "parent_id": None,
            "module": "real_estate",
            "slug": {"tr": "test-category", "de": "test-kategorie", "fr": "test-categorie"},
            "icon": "building",
            "allowed_countries": ["DE", "CH"],
            "is_enabled": True,
            "translations": [
                {"language": "tr", "name": "Test Category", "description": "Test description"},
                {"language": "de", "name": "Test Kategorie", "description": "Test Beschreibung"},
                {"language": "fr", "name": "Test Catégorie", "description": "Test description"}
            ]
        }
        
        success, data = self.run_test(
            "Create Test Category",
            "POST",
            "/categories",
            201,
            data=category_data
        )
        
        if success:
            print(f"   Created category with ID: {data.get('id')}")
            return data.get('id')
        return None

    def test_create_attribute(self):
        """Test creating a new attribute"""
        attribute_data = {
            "key": "test_attribute",
            "name": {"tr": "Test Attribute", "de": "Test Attribut", "fr": "Test Attribut"},
            "attribute_type": "text",
            "is_required": False,
            "is_filterable": True,
            "is_sortable": False,
            "unit": "m²",
            "options": []
        }
        
        success, data = self.run_test(
            "Create Test Attribute", 
            "POST",
            "/attributes",
            201,
            data=attribute_data
        )
        
        if success:
            print(f"   Created attribute with ID: {data.get('id')}")
            return data.get('id')
        return None

def main():
    print("🚀 Starting Extended Admin Panel API Tests")
    print("=" * 60)
    
    tester = ExtendedAdminAPITester()
    
    # Login first
    if not tester.login_admin():
        print("❌ Login failed, stopping tests")
        return 1
    
    # Test P0 endpoints
    print("\n🏢 Testing Categories...")
    category_results = tester.test_categories_by_module()
    tester.test_category_tree()
    
    print("\n⚙️ Testing Attributes...")
    attribute_results = tester.test_attributes_by_type()
    
    print("\n📋 Testing Menu Manager...")
    menu_success, menu_data = tester.test_menu_top_items()
    
    print("\n🏠 Testing Home Layout...")
    tester.test_home_layout_endpoints()
    
    print("\n➕ Testing Creation Endpoints...")
    category_id = tester.test_create_category()
    attribute_id = tester.test_create_attribute()
    
    # Print results
    print("\n" + "=" * 60)
    print(f"📊 Tests completed: {tester.tests_passed}/{tester.tests_run}")
    
    print(f"\n📈 Category Summary:")
    for module, count in category_results.items():
        print(f"   {module}: {count} categories")
        
    print(f"\n🔧 Attribute Summary:")
    for attr_type, count in attribute_results.items():
        print(f"   {attr_type}: {count} attributes")
    
    if tester.failures:
        print(f"\n❌ Failed tests ({len(tester.failures)}):")
        for failure in tester.failures:
            error_msg = failure.get('error', f'Status {failure.get("actual")} != {failure.get("expected")}')
            print(f"  • {failure['test']}: {error_msg}")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"\n📈 Success rate: {success_rate:.1f}%")
    
    return 0 if success_rate >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())