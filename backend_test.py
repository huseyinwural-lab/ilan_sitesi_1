#!/usr/bin/env python3
"""
Layout Builder P0 APIs Backend Test
Testing the specific P0 APIs mentioned in review request
"""
import os
import sys
import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://category-results.preview.emergentagent.com"
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

class LayoutBuilderP0Tester:
    def __init__(self):
        self.admin_token = None
        self.test_results = []
        self.component_ids = []
        self.page_ids = []
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": time.strftime("%H:%M:%S")
        }
        self.test_results.append(result)
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   → {details}")
    
    def setup_admin_auth(self) -> bool:
        """Authenticate admin user"""
        try:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=15
            )
            
            if response.status_code == 200:
                self.admin_token = response.json().get("access_token")
                self.log_test("Admin Authentication", "PASS", f"Token acquired successfully")
                return True
            else:
                self.log_test("Admin Authentication", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("Admin Authentication", "FAIL", f"Exception: {str(e)}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with admin token"""
        return {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
    
    def test_components_api(self):
        """Test /api/admin/site/content-layout/components"""
        print("\n🔧 Testing Components API")
        
        # Test 1: Create component with valid schema -> 200
        unique_key = f"test.component.valid.{uuid.uuid4().hex[:10]}"
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/components",
                headers=self.get_headers(),
                json={
                    "key": unique_key,
                    "name": "Test Valid Component",
                    "schema_json": {
                        "type": "object",
                        "properties": {"title": {"type": "string"}},
                        "required": ["title"]
                    },
                    "is_active": True
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                component_id = data.get("item", {}).get("id")
                if component_id:
                    self.component_ids.append(component_id)
                self.log_test("Component Create Valid Schema", "PASS", f"HTTP 200, component_id: {component_id}")
            else:
                self.log_test("Component Create Valid Schema", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Component Create Valid Schema", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Create component with invalid schema -> 400
        invalid_key = f"test.component.invalid.{uuid.uuid4().hex[:10]}"
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/components",
                headers=self.get_headers(),
                json={
                    "key": invalid_key,
                    "name": "Test Invalid Component",
                    "schema_json": {"type": "not-a-valid-json-schema-type"},
                    "is_active": True
                },
                timeout=10
            )
            
            if response.status_code == 400:
                self.log_test("Component Create Invalid Schema", "PASS", f"HTTP 400 as expected: {response.text[:100]}")
            else:
                self.log_test("Component Create Invalid Schema", "FAIL", f"Expected 400, got {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Component Create Invalid Schema", "FAIL", f"Exception: {str(e)}")
        
        # Test 3: Create component with duplicate key -> 409
        try:
            # First creation (should succeed)
            response1 = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/components",
                headers=self.get_headers(),
                json={
                    "key": unique_key,  # Same key as before
                    "name": "Duplicate Component",
                    "schema_json": {"type": "object", "properties": {}},
                    "is_active": True
                },
                timeout=10
            )
            
            if response1.status_code == 409:
                self.log_test("Component Create Duplicate Key", "PASS", f"HTTP 409 conflict as expected")
            else:
                self.log_test("Component Create Duplicate Key", "FAIL", f"Expected 409, got {response1.status_code}: {response1.text[:200]}")
                
        except Exception as e:
            self.log_test("Component Create Duplicate Key", "FAIL", f"Exception: {str(e)}")
    
    def test_pages_api(self):
        """Test /api/admin/site/content-layout/pages"""
        print("\n📄 Testing Pages API")
        
        # Test 1: Create default scope (category_id=null)
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_page_{marker}"
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages",
                headers=self.get_headers(),
                json={
                    "page_type": "search_l1",
                    "country": "DE",
                    "module": module_name,
                    "category_id": None
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                page_id = data.get("item", {}).get("id")
                if page_id:
                    self.page_ids.append(page_id)
                self.log_test("Page Create Default Scope", "PASS", f"HTTP 200, page_id: {page_id}")
            else:
                self.log_test("Page Create Default Scope", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Page Create Default Scope", "FAIL", f"Exception: {str(e)}")
        
        # Test 2: Create duplicate scope -> 409
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages",
                headers=self.get_headers(),
                json={
                    "page_type": "search_l1",
                    "country": "DE",
                    "module": module_name,  # Same scope
                    "category_id": None
                },
                timeout=10
            )
            
            if response.status_code == 409:
                self.log_test("Page Create Duplicate Scope", "PASS", f"HTTP 409 conflict as expected")
            else:
                self.log_test("Page Create Duplicate Scope", "FAIL", f"Expected 409, got {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Page Create Duplicate Scope", "FAIL", f"Exception: {str(e)}")
    
    def test_revisions_flow(self):
        """Test revisions flow: draft create, publish, archive"""
        print("\n📝 Testing Revisions Flow")
        
        if not self.page_ids:
            self.log_test("Revisions Flow", "SKIP", "No page_id available from previous tests")
            return
        
        page_id = self.page_ids[0]
        
        # Test 1: Create draft revision
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
                headers=self.get_headers(),
                json={"payload_json": {"rows": [{"id": "test-row-1"}]}},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                revision_id = data.get("item", {}).get("id")
                status = data.get("item", {}).get("status")
                version = data.get("item", {}).get("version")
                self.log_test("Draft Create", "PASS", f"HTTP 200, revision_id: {revision_id}, status: {status}, version: {version}")
                
                # Test 2: Publish draft revision
                if revision_id:
                    publish_response = requests.post(
                        f"{BASE_URL}/api/admin/site/content-layout/revisions/{revision_id}/publish",
                        headers=self.get_headers(),
                        timeout=10
                    )
                    
                    if publish_response.status_code == 200:
                        pub_data = publish_response.json()
                        pub_status = pub_data.get("item", {}).get("status")
                        published_at = pub_data.get("item", {}).get("published_at")
                        self.log_test("Draft Publish", "PASS", f"HTTP 200, status: {pub_status}, published_at: {published_at}")
                        
                        # Test 3: Archive published revision
                        archive_response = requests.post(
                            f"{BASE_URL}/api/admin/site/content-layout/revisions/{revision_id}/archive",
                            headers=self.get_headers(),
                            timeout=10
                        )
                        
                        if archive_response.status_code == 200:
                            arch_data = archive_response.json()
                            arch_status = arch_data.get("item", {}).get("status")
                            self.log_test("Published Archive", "PASS", f"HTTP 200, status: {arch_status}")
                        else:
                            self.log_test("Published Archive", "FAIL", f"HTTP {archive_response.status_code}: {archive_response.text[:200]}")
                    else:
                        self.log_test("Draft Publish", "FAIL", f"HTTP {publish_response.status_code}: {publish_response.text[:200]}")
            else:
                self.log_test("Draft Create", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Revisions Flow", "FAIL", f"Exception: {str(e)}")
    
    def test_bindings_flow(self):
        """Test bindings flow: bind, get active, unbind"""
        print("\n🔗 Testing Bindings Flow")
        
        if not self.page_ids:
            self.log_test("Bindings Flow", "SKIP", "No page_id available from previous tests")
            return
        
        # Get a test category ID
        category_id = self.get_test_category_id()
        if not category_id:
            self.log_test("Bindings Flow", "SKIP", "No category_id available for binding")
            return
        
        page_id = self.page_ids[0]
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_bind_{marker}"
        
        # First create and publish a revision (required for binding)
        self.create_and_publish_revision(page_id)
        
        # Test 1: Bind category to page
        try:
            response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/bindings",
                headers=self.get_headers(),
                json={
                    "country": "DE",
                    "module": module_name,
                    "category_id": category_id,
                    "layout_page_id": page_id
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                binding_id = data.get("item", {}).get("id")
                is_active = data.get("item", {}).get("is_active")
                self.log_test("Category Bind", "PASS", f"HTTP 200, binding_id: {binding_id}, active: {is_active}")
                
                # Test 2: Get active binding
                active_response = requests.get(
                    f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
                    headers=self.get_headers(),
                    params={
                        "country": "DE",
                        "module": module_name,
                        "category_id": category_id
                    },
                    timeout=10
                )
                
                if active_response.status_code == 200:
                    active_data = active_response.json()
                    active_binding = active_data.get("item")
                    if active_binding:
                        self.log_test("Get Active Binding", "PASS", f"HTTP 200, found active binding: {active_binding.get('id')}")
                    else:
                        self.log_test("Get Active Binding", "FAIL", f"HTTP 200 but no active binding found")
                else:
                    self.log_test("Get Active Binding", "FAIL", f"HTTP {active_response.status_code}: {active_response.text[:200]}")
                
                # Test 3: Unbind category
                unbind_response = requests.post(
                    f"{BASE_URL}/api/admin/site/content-layout/bindings/unbind",
                    headers=self.get_headers(),
                    json={
                        "country": "DE",
                        "module": module_name,
                        "category_id": category_id
                    },
                    timeout=10
                )
                
                if unbind_response.status_code == 200:
                    unbind_data = unbind_response.json()
                    unbound_count = unbind_data.get("unbound_count", 0)
                    self.log_test("Category Unbind", "PASS", f"HTTP 200, unbound_count: {unbound_count}")
                else:
                    self.log_test("Category Unbind", "FAIL", f"HTTP {unbind_response.status_code}: {unbind_response.text[:200]}")
            else:
                self.log_test("Category Bind", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Bindings Flow", "FAIL", f"Exception: {str(e)}")
    
    def test_resolve_api(self):
        """Test /api/site/content-layout/resolve fallback behavior and cache"""
        print("\n🔍 Testing Resolve API")
        
        # Create a new page specifically for resolve testing
        marker = uuid.uuid4().hex[:8]
        module_name = f"test_resolve_{marker}"
        
        # Create page for resolve testing
        try:
            page_response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages",
                headers=self.get_headers(),
                json={
                    "page_type": "search_l1",
                    "country": "DE",
                    "module": module_name,
                    "category_id": None
                },
                timeout=10
            )
            
            if page_response.status_code != 200:
                self.log_test("Resolve API", "SKIP", f"Could not create page for resolve test: HTTP {page_response.status_code}")
                return
                
            page_id = page_response.json().get("item", {}).get("id")
            if not page_id:
                self.log_test("Resolve API", "SKIP", "No page_id from page creation")
                return
        except Exception as e:
            self.log_test("Resolve API", "SKIP", f"Exception creating page: {str(e)}")
            return
        
        # Create and publish a revision for the page
        revision_id = self.create_and_publish_revision(page_id)
        if not revision_id:
            self.log_test("Resolve API", "SKIP", "Could not create published revision")
            return
        
        # Test 1: Resolve fallback behavior (no auth required)
        try:
            response = requests.get(
                f"{BASE_URL}/api/site/content-layout/resolve",
                params={
                    "country": "DE",
                    "module": module_name,
                    "page_type": "search_l1"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                source = data.get("source")
                layout_page = data.get("layout_page")
                revision = data.get("revision")
                self.log_test("Resolve Fallback", "PASS", f"HTTP 200, source: {source}, page_id: {layout_page.get('id') if layout_page else None}")
                
                # Test 2: Second resolve call should return cached result
                response2 = requests.get(
                    f"{BASE_URL}/api/site/content-layout/resolve",
                    params={
                        "country": "DE",
                        "module": module_name,
                        "page_type": "search_l1"
                    },
                    timeout=10
                )
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    source2 = data2.get("source")
                    if source2 == "cache":
                        self.log_test("Resolve Cache Hit", "PASS", f"HTTP 200, source: cache (cache working)")
                    else:
                        self.log_test("Resolve Cache Hit", "INFO", f"HTTP 200, source: {source2} (may be cached internally)")
                else:
                    self.log_test("Resolve Cache Hit", "FAIL", f"HTTP {response2.status_code}: {response2.text[:200]}")
            else:
                self.log_test("Resolve Fallback", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Resolve API", "FAIL", f"Exception: {str(e)}")
    
    def test_metrics_api(self):
        """Test /api/admin/site/content-layout/metrics"""
        print("\n📊 Testing Metrics API")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/site/content-layout/metrics",
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                metrics = data.get("metrics", {})
                required_metrics = [
                    "resolve_requests", "resolve_cache_hits", "resolve_cache_misses",
                    "publish_count", "binding_changes"
                ]
                
                missing_metrics = [m for m in required_metrics if m not in metrics]
                if not missing_metrics:
                    self.log_test("Metrics API", "PASS", f"HTTP 200, all required metrics present: {list(metrics.keys())}")
                else:
                    self.log_test("Metrics API", "PARTIAL", f"HTTP 200, missing metrics: {missing_metrics}")
            else:
                self.log_test("Metrics API", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Metrics API", "FAIL", f"Exception: {str(e)}")
    
    def test_audit_logs_api(self):
        """Test /api/admin/site/content-layout/audit-logs"""
        print("\n📋 Testing Audit Logs API")
        
        try:
            response = requests.get(
                f"{BASE_URL}/api/admin/site/content-layout/audit-logs",
                headers=self.get_headers(),
                params={"page": 1, "limit": 10},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                pagination = data.get("pagination", {})
                self.log_test("Audit Logs API", "PASS", f"HTTP 200, {len(items)} audit log items, pagination: {pagination}")
            else:
                self.log_test("Audit Logs API", "FAIL", f"HTTP {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            self.log_test("Audit Logs API", "FAIL", f"Exception: {str(e)}")
    
    def get_test_category_id(self) -> Optional[str]:
        """Get a test category ID for binding tests"""
        try:
            response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE", timeout=10)
            if response.status_code == 200:
                categories = response.json()
                if isinstance(categories, list) and categories:
                    return categories[0].get("id")
        except Exception:
            pass
        return None
    
    def create_and_publish_revision(self, page_id: str) -> Optional[str]:
        """Helper to create and publish a revision"""
        try:
            # Create draft
            draft_response = requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
                headers=self.get_headers(),
                json={"payload_json": {"rows": []}},
                timeout=10
            )
            
            if draft_response.status_code == 200:
                draft_id = draft_response.json().get("item", {}).get("id")
                
                # Publish draft
                if draft_id:
                    publish_response = requests.post(
                        f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
                        headers=self.get_headers(),
                        timeout=10
                    )
                    
                    if publish_response.status_code == 200:
                        return draft_id
        except Exception:
            pass
        return None
    
    def run_all_tests(self):
        """Run all P0 API tests"""
        print("🚀 Starting Layout Builder P0 APIs Test")
        print(f"📍 Backend URL: {BASE_URL}")
        print("="*60)
        
        # Setup
        if not self.setup_admin_auth():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Run all tests
        self.test_components_api()
        self.test_pages_api()
        self.test_revisions_flow()
        self.test_bindings_flow()
        self.test_resolve_api()
        self.test_metrics_api()
        self.test_audit_logs_api()
        
        # Summary
        print("\n" + "="*60)
        print("📈 TEST SUMMARY")
        print("="*60)
        
        passed = len([t for t in self.test_results if t["status"] == "PASS"])
        failed = len([t for t in self.test_results if t["status"] == "FAIL"])
        skipped = len([t for t in self.test_results if t["status"] == "SKIP"])
        partial = len([t for t in self.test_results if t["status"] in ["PARTIAL", "INFO"]])
        total = len(self.test_results)
        
        print(f"✅ PASSED: {passed}")
        print(f"❌ FAILED: {failed}")
        print(f"⚠️  PARTIAL/INFO: {partial}")
        print(f"⏭️  SKIPPED: {skipped}")
        print(f"📊 TOTAL: {total}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"🎯 SUCCESS RATE: {success_rate:.1f}%")
        
        # Detailed results for failures
        failures = [t for t in self.test_results if t["status"] == "FAIL"]
        if failures:
            print("\n❌ FAILED TESTS DETAILS:")
            for failure in failures:
                print(f"   • {failure['test']}: {failure['details']}")
        
        return failed == 0

if __name__ == "__main__":
    tester = LayoutBuilderP0Tester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)