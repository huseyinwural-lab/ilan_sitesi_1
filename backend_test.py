#!/usr/bin/env python3
"""
Backend Smoke Test + Validation for Turkish Review Request
Testing:
1. Admin login ve user login çalışıyor mu
2. /api/admin/finance/overview endpoint 200 ve cards alanları dönüyor mu
3. /api/admin/finance/subscriptions ve /api/admin/finance/ledger endpointleri 200 veriyor mu
4. /api/admin/payments/export/csv, /api/admin/invoices/export/csv, /api/admin/ledger/export/csv 
   sadece super_admin için 200; normal user için 403 doğrula
5. /api/admin/invoices create ile amount_minor/net_minor/tax_minor/gross_minor alanları dolu dönüyor mu
"""

import requests
import json
import sys
from datetime import datetime
import uuid

# Backend URL from environment
BACKEND_URL = "https://billing-cleanup.preview.emergentagent.com"

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "admin@platform.com",
    "password": "Admin123!"
}

USER_CREDENTIALS = {
    "email": "user@platform.com", 
    "password": "User123!"
}

class BackendTester:
    def __init__(self):
        self.admin_token = None
        self.user_token = None
        self.results = {
            "admin_login": False,
            "user_login": False,
            "finance_overview": False,
            "finance_subscriptions": False,
            "finance_ledger": False,
            "csv_exports_admin": False,
            "csv_exports_user_403": False,
            "invoice_create": False
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Backend-Test/1.0',
            'Content-Type': 'application/json'
        })

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def test_admin_login(self):
        """Test 1: Admin login çalışıyor mu"""
        self.log("🔐 Testing Admin Login...")
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=ADMIN_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data or 'access_token' in data:
                    # Try both possible token fields
                    self.admin_token = data.get('token') or data.get('access_token')
                    
                    # Check if user has admin role
                    user_role = data.get('role', 'unknown')
                    self.log(f"✅ Admin login SUCCESS - Token received (length: {len(self.admin_token)}), Role: {user_role}")
                    self.results["admin_login"] = True
                else:
                    self.log(f"❌ Admin login FAILED - No token in response: {data}")
            else:
                self.log(f"❌ Admin login FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ Admin login ERROR: {str(e)}")

    def test_user_login(self):
        """Test 1: User login çalışıyor mu"""
        self.log("🔐 Testing User Login...")
        try:
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=USER_CREDENTIALS,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'token' in data or 'access_token' in data:
                    self.user_token = data.get('token') or data.get('access_token')
                    self.log(f"✅ User login SUCCESS - Token received (length: {len(self.user_token)})")
                    self.results["user_login"] = True
                else:
                    self.log(f"❌ User login FAILED - No token in response: {data}")
            else:
                self.log(f"❌ User login FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ User login ERROR: {str(e)}")

    def test_finance_overview(self):
        """Test 2: /api/admin/finance/overview endpoint 200 ve cards alanları dönüyor mu"""
        if not self.admin_token:
            self.log("⏭️ Skipping finance overview - no admin token")
            return
            
        self.log("💰 Testing Finance Overview Endpoint...")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/api/admin/finance/overview",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'cards' in data:
                    cards = data['cards']
                    self.log(f"✅ Finance Overview SUCCESS - Status: 200, Cards field present with {len(cards)} cards")
                    
                    # Log some card details for verification
                    try:
                        for i, card in enumerate(cards[:3]):  # Show first 3 cards
                            if isinstance(card, dict):
                                title = card.get('title', 'No title')
                                value = card.get('value', 'No value')
                            else:
                                title = str(card)
                                value = "N/A"
                            self.log(f"   📊 Card {i+1}: {title} = {value}")
                    except Exception as card_error:
                        self.log(f"   📊 Cards present but structure differs: {type(cards)} with {len(cards)} items")
                    
                    self.results["finance_overview"] = True
                else:
                    self.log(f"❌ Finance Overview FAILED - No 'cards' field in response: {list(data.keys())}")
            else:
                self.log(f"❌ Finance Overview FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ Finance Overview ERROR: {str(e)}")

    def test_finance_subscriptions(self):
        """Test 3: /api/admin/finance/subscriptions endpoint 200 veriyor mu"""
        if not self.admin_token:
            self.log("⏭️ Skipping finance subscriptions - no admin token")
            return
            
        self.log("📊 Testing Finance Subscriptions Endpoint...")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/api/admin/finance/subscriptions",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Finance Subscriptions SUCCESS - Status: 200, Response size: {len(str(data))} chars")
                self.results["finance_subscriptions"] = True
            else:
                self.log(f"❌ Finance Subscriptions FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ Finance Subscriptions ERROR: {str(e)}")

    def test_finance_ledger(self):
        """Test 3: /api/admin/finance/ledger endpoint 200 veriyor mu"""
        if not self.admin_token:
            self.log("⏭️ Skipping finance ledger - no admin token")
            return
            
        self.log("📋 Testing Finance Ledger Endpoint...")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/api/admin/finance/ledger",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Finance Ledger SUCCESS - Status: 200, Response size: {len(str(data))} chars")
                self.results["finance_ledger"] = True
            else:
                self.log(f"❌ Finance Ledger FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ Finance Ledger ERROR: {str(e)}")

    def test_csv_exports(self):
        """Test 4: CSV export endpoints - super_admin için 200, normal user için 403"""
        if not self.admin_token:
            self.log("⏭️ Skipping CSV exports - no admin token")
            return
            
        export_endpoints = [
            "/api/admin/payments/export/csv",
            "/api/admin/invoices/export/csv", 
            "/api/admin/ledger/export/csv"
        ]
        
        self.log("📤 Testing CSV Export Endpoints for Admin (expect 200)...")
        admin_success_count = 0
        
        for endpoint in export_endpoints:
            try:
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                response = self.session.get(
                    f"{BACKEND_URL}{endpoint}",
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    self.log(f"✅ Admin CSV Export SUCCESS - {endpoint}: 200")
                    admin_success_count += 1
                else:
                    self.log(f"❌ Admin CSV Export FAILED - {endpoint}: {response.status_code}")
            except Exception as e:
                self.log(f"❌ Admin CSV Export ERROR - {endpoint}: {str(e)}")
        
        if admin_success_count == len(export_endpoints):
            self.results["csv_exports_admin"] = True
            self.log(f"✅ All {len(export_endpoints)} CSV exports work for admin")
        
        # Test with user token (expect 403)
        if self.user_token:
            self.log("📤 Testing CSV Export Endpoints for User (expect 403)...")
            user_403_count = 0
            
            for endpoint in export_endpoints:
                try:
                    headers = {"Authorization": f"Bearer {self.user_token}"}
                    response = self.session.get(
                        f"{BACKEND_URL}{endpoint}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if response.status_code == 403:
                        self.log(f"✅ User CSV Export BLOCKED - {endpoint}: 403 (correct)")
                        user_403_count += 1
                    else:
                        self.log(f"❌ User CSV Export SECURITY ISSUE - {endpoint}: {response.status_code} (should be 403)")
                except Exception as e:
                    self.log(f"❌ User CSV Export ERROR - {endpoint}: {str(e)}")
            
            if user_403_count == len(export_endpoints):
                self.results["csv_exports_user_403"] = True
                self.log(f"✅ All {len(export_endpoints)} CSV exports correctly blocked for user")
        else:
            self.log("⏭️ Skipping user CSV export test - no user token")

    def test_invoice_create(self):
        """Test 5: /api/admin/invoices create ile amount_minor/net_minor/tax_minor/gross_minor alanları dolu dönüyor mu"""
        if not self.admin_token:
            self.log("⏭️ Skipping invoice create - no admin token")
            return
            
        self.log("🧾 Testing Invoice Create Endpoint...")
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # First, try to get current user info to use existing user_id
            user_response = self.session.get(
                f"{BACKEND_URL}/api/auth/me",
                headers=headers,
                timeout=30
            )
            
            user_id = None
            if user_response.status_code == 200:
                user_data = user_response.json()
                user_id = user_data.get('id') or user_data.get('user_id')
            
            # If no user_id found, use a known test user email
            if not user_id:
                user_id = "admin@platform.com"  # Use email as fallback
            
            # Create a test invoice with existing user_id
            invoice_data = {
                "user_id": user_id,
                "customer_name": "Test Customer",
                "customer_email": "test@example.com",
                "amount": 12500,  # 125.00 in minor units (cents)
                "currency": "EUR",
                "due_date": "2024-03-15",
                "description": "Backend test invoice"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/admin/invoices",
                headers=headers,
                json=invoice_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                
                # The response might have an 'invoice' wrapper object
                invoice_data = data.get('invoice', data)
                
                # Check for required minor amount fields
                required_fields = ['amount_minor', 'net_minor', 'tax_minor', 'gross_minor']
                found_fields = []
                missing_fields = []
                
                for field in required_fields:
                    if field in invoice_data and invoice_data[field] is not None:
                        found_fields.append(f"{field}={invoice_data[field]}")
                    else:
                        missing_fields.append(field)
                
                if not missing_fields:
                    self.log(f"✅ Invoice Create SUCCESS - All minor amount fields present: {', '.join(found_fields)}")
                    self.results["invoice_create"] = True
                else:
                    self.log(f"❌ Invoice Create FAILED - Missing fields: {missing_fields}")
                    self.log(f"   Found fields: {found_fields}")
                    self.log(f"   Response keys: {list(data.keys())}")
                    if 'invoice' in data:
                        self.log(f"   Invoice keys: {list(invoice_data.keys())}")
                    
            else:
                self.log(f"❌ Invoice Create FAILED - Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log(f"❌ Invoice Create ERROR: {str(e)}")

    def run_all_tests(self):
        """Run all backend smoke tests"""
        self.log("🚀 Starting Backend Smoke + Validation Tests")
        self.log(f"Backend URL: {BACKEND_URL}")
        
        # Test 1: Login functionality 
        self.test_admin_login()
        self.test_user_login()
        
        # Test 2: Finance overview
        self.test_finance_overview()
        
        # Test 3: Finance subscriptions and ledger
        self.test_finance_subscriptions()
        self.test_finance_ledger()
        
        # Test 4: CSV exports
        self.test_csv_exports()
        
        # Test 5: Invoice creation
        self.test_invoice_create()
        
        return self.generate_report()

    def generate_report(self):
        """Generate final test report"""
        self.log("\n" + "="*60)
        self.log("📋 BACKEND SMOKE + VALIDATION REPORT")
        self.log("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results.values() if result)
        
        # Individual test results
        test_descriptions = {
            "admin_login": "1️⃣ Admin Login",
            "user_login": "1️⃣ User Login", 
            "finance_overview": "2️⃣ Finance Overview (/api/admin/finance/overview) - 200 + cards field",
            "finance_subscriptions": "3️⃣ Finance Subscriptions (/api/admin/finance/subscriptions) - 200",
            "finance_ledger": "3️⃣ Finance Ledger (/api/admin/finance/ledger) - 200",
            "csv_exports_admin": "4️⃣ CSV Exports for Super Admin - 200",
            "csv_exports_user_403": "4️⃣ CSV Exports for Normal User - 403",
            "invoice_create": "5️⃣ Invoice Create - amount_minor/net_minor/tax_minor/gross_minor fields"
        }
        
        for test_key, description in test_descriptions.items():
            status = "✅ PASS" if self.results[test_key] else "❌ FAIL"
            self.log(f"{status} - {description}")
        
        self.log("-" * 60)
        self.log(f"📊 SUMMARY: {passed_tests}/{total_tests} tests passed ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - Backend is functioning correctly!")
            return "PASS"
        else:
            failed_count = total_tests - passed_tests
            self.log(f"⚠️  {failed_count} TEST(S) FAILED - Issues detected in backend")
            return "FAIL"

if __name__ == "__main__":
    tester = BackendTester()
    result = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if result == "PASS" else 1)