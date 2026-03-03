"""
P1.1 Granular Permission Yönetim UI - Backend Tests
Acceptance Criteria:
- Backend permission admin endpoints: /api/admin/permissions/*
- CRUD: 5 örnek user üzerinde grant/revoke işlemleri PASS  
- Security guards: self-edit forbidden, super_admin revoke forbidden, unauthorized 403
- Shadow diff doğrulaması: diff_count=0
- Audit linkage: permission mutation sonrası audit endpointinden filtrelenebilir kayıt erişimi
"""
import pytest
import requests
import os

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestPermissionAuth:
    """Test login for different user roles"""
    
    def test_super_admin_login(self):
        """super_admin can login successfully"""
        for attempt in range(3):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "admin@platform.com",
                "password": "Admin123!"
            })
            if response.status_code != 502:
                break
            import time
            time.sleep(2)
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "super_admin"
        
    def test_user_login(self):
        """individual user can login successfully"""
        for attempt in range(3):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "user@platform.com",
                "password": "User123!"
            })
            if response.status_code != 502:
                break
            import time
            time.sleep(2)
        assert response.status_code == 200, f"User login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "individual"
        
    def test_dealer_login(self):
        """dealer can login successfully"""
        for attempt in range(3):
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "dealer@platform.com",
                "password": "Dealer123!"
            })
            if response.status_code != 502:
                break
            import time
            time.sleep(2)
        assert response.status_code == 200, f"Dealer login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["user"]["role"] == "dealer"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@platform.com",
        "password": "Admin123!"
    })
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def user_token():
    """Get individual user auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "user@platform.com",
        "password": "User123!"
    })
    if response.status_code != 200:
        pytest.skip(f"User login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "dealer@platform.com",
        "password": "Dealer123!"
    })
    if response.status_code != 200:
        pytest.skip(f"Dealer login failed: {response.text}")
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_user_id(admin_token):
    """Get admin user ID"""
    response = requests.get(f"{BASE_URL}/api/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    if response.status_code != 200:
        pytest.skip("Could not get admin user details")
    return response.json()["id"]


class TestPermissionEndpoints:
    """Test permission admin endpoints"""
    
    def test_permissions_flags_endpoint(self, admin_token):
        """GET /admin/permissions/flags returns permission flags config"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/flags", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Flags endpoint failed: {response.text}"
        data = response.json()
        assert "domains" in data
        assert "fallback_matrix" in data
        assert "finance" in data["domains"]
        assert "content" in data["domains"]
        print(f"PASS: Flags endpoint returned domains: {list(data['domains'].keys())}")
        
    def test_permissions_users_endpoint(self, admin_token):
        """GET /admin/permissions/users returns user list"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Users endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "count" in data
        assert len(data["items"]) > 0
        print(f"PASS: Users endpoint returned {data['count']} users")
        
    def test_permissions_overrides_endpoint(self, admin_token):
        """GET /admin/permissions/overrides returns override list"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/overrides", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Overrides endpoint failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "count" in data
        print(f"PASS: Overrides endpoint returned {data['count']} overrides")
        
    def test_permissions_shadow_diff_endpoint(self, admin_token):
        """GET /admin/permissions/shadow-diff returns diff count"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/shadow-diff", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Shadow diff endpoint failed: {response.text}"
        data = response.json()
        assert "diff_count" in data
        assert "checked_user_count" in data
        # Acceptance criteria: diff_count should be 0
        assert data["diff_count"] == 0, f"Shadow diff count is not 0: {data['diff_count']}"
        print(f"PASS: Shadow diff = 0, checked {data['checked_user_count']} users")


class TestUnauthorizedAccess:
    """Test unauthorized access returns 403"""
    
    def test_user_cannot_access_permissions_flags(self, user_token):
        """Individual user cannot access /admin/permissions/flags - returns 403"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/flags", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert response.status_code == 403, f"Expected 403 for user access, got {response.status_code}"
        print("PASS: User gets 403 on /admin/permissions/flags")
        
    def test_user_cannot_access_permissions_users(self, user_token):
        """Individual user cannot access /admin/permissions/users - returns 403"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/users", headers={
            "Authorization": f"Bearer {user_token}"
        })
        assert response.status_code == 403, f"Expected 403 for user access, got {response.status_code}"
        print("PASS: User gets 403 on /admin/permissions/users")
        
    def test_dealer_cannot_access_permissions_flags(self, dealer_token):
        """Dealer cannot access /admin/permissions/flags - returns 403"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/flags", headers={
            "Authorization": f"Bearer {dealer_token}"
        })
        assert response.status_code == 403, f"Expected 403 for dealer access, got {response.status_code}"
        print("PASS: Dealer gets 403 on /admin/permissions/flags")
        
    def test_dealer_cannot_access_permissions_users(self, dealer_token):
        """Dealer cannot access /admin/permissions/users - returns 403"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/users", headers={
            "Authorization": f"Bearer {dealer_token}"
        })
        assert response.status_code == 403, f"Expected 403 for dealer access, got {response.status_code}"
        print("PASS: Dealer gets 403 on /admin/permissions/users")
        
    def test_user_cannot_grant_permission(self, user_token):
        """Individual user cannot grant permissions - returns 403"""
        response = requests.post(f"{BASE_URL}/api/admin/permissions/grant", 
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "target_user_id": "00000000-0000-0000-0000-000000000001",
                "domain": "finance",
                "action": "view",
                "country_scope": [],
                "reason": "Test reason for unauthorized grant attempt"
            }
        )
        assert response.status_code == 403, f"Expected 403 for user grant, got {response.status_code}"
        print("PASS: User gets 403 on grant attempt")
        
    def test_dealer_cannot_grant_permission(self, dealer_token):
        """Dealer cannot grant permissions - returns 403"""
        response = requests.post(f"{BASE_URL}/api/admin/permissions/grant", 
            headers={"Authorization": f"Bearer {dealer_token}"},
            json={
                "target_user_id": "00000000-0000-0000-0000-000000000001",
                "domain": "finance",
                "action": "view",
                "country_scope": [],
                "reason": "Test reason for unauthorized grant attempt"
            }
        )
        assert response.status_code == 403, f"Expected 403 for dealer grant, got {response.status_code}"
        print("PASS: Dealer gets 403 on grant attempt")


class TestSecurityGuards:
    """Test security guards: self-edit forbidden, super_admin revoke forbidden"""
    
    def test_self_edit_forbidden(self, admin_token, admin_user_id):
        """Admin cannot grant permissions to themselves - returns 403"""
        response = requests.post(f"{BASE_URL}/api/admin/permissions/grant", 
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": admin_user_id,
                "domain": "finance",
                "action": "view",
                "country_scope": [],
                "reason": "Test reason for self grant attempt - should fail"
            }
        )
        assert response.status_code == 403, f"Expected 403 for self-edit, got {response.status_code}"
        data = response.json()
        assert "forbidden" in data.get("detail", "").lower(), f"Expected 'forbidden' message, got: {data}"
        print("PASS: Self-edit is forbidden (403)")
        
    def test_super_admin_revoke_forbidden(self, admin_token):
        """Cannot revoke permissions from super_admin - returns 403"""
        # First get the super_admin user ID (admin@platform.com)
        users_response = requests.get(f"{BASE_URL}/api/admin/permissions/users?role=super_admin", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert users_response.status_code == 200
        users_data = users_response.json()
        
        # Find any super_admin user
        super_admin_user = None
        for user in users_data.get("items", []):
            if user.get("role") == "super_admin":
                super_admin_user = user
                break
                
        if not super_admin_user:
            pytest.skip("No super_admin user found for testing revoke forbidden")
            
        # Try to revoke - should get 403
        response = requests.post(f"{BASE_URL}/api/admin/permissions/revoke", 
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": super_admin_user["id"],
                "domain": "finance",
                "action": "view",
                "reason": "Test reason for super_admin revoke attempt - should fail"
            }
        )
        assert response.status_code == 403, f"Expected 403 for super_admin revoke, got {response.status_code}"
        print("PASS: Super admin revoke is forbidden (403)")


class TestGrantRevokeCRUD:
    """Test Grant/Revoke CRUD on 5 sample users"""
    
    def test_grant_revoke_flow(self, admin_token):
        """Test grant and revoke flow on sample users"""
        # Get list of users for testing
        users_response = requests.get(f"{BASE_URL}/api/admin/permissions/users?limit=20", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert users_response.status_code == 200
        users_data = users_response.json()
        
        # Filter out super_admin users (can't revoke from them) and get 5 sample users
        sample_users = []
        for user in users_data.get("items", []):
            if user.get("role") != "super_admin" and len(sample_users) < 5:
                sample_users.append(user)
                
        if len(sample_users) < 5:
            print(f"WARNING: Only found {len(sample_users)} non-super_admin users for testing")
            if len(sample_users) == 0:
                pytest.skip("No suitable users found for grant/revoke testing")
        
        # Test domains and actions
        test_cases = [
            ("finance", "view"),
            ("content", "edit"),
            ("finance", "export"),
            ("content", "publish"),
            ("finance", "delete"),
        ]
        
        results = []
        for idx, user in enumerate(sample_users):
            domain, action = test_cases[idx % len(test_cases)]
            user_id = user["id"]
            user_email = user["email"]
            user_role = user["role"]
            
            # Grant permission
            grant_response = requests.post(f"{BASE_URL}/api/admin/permissions/grant",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_user_id": user_id,
                    "domain": domain,
                    "action": action,
                    "country_scope": [],
                    "reason": f"P1.1 test grant for {user_email} - domain={domain} action={action}"
                }
            )
            grant_status = grant_response.status_code
            grant_ok = grant_status == 200
            
            if not grant_ok:
                results.append({
                    "user_email": user_email,
                    "role": user_role,
                    "domain": domain,
                    "action": action,
                    "grant_status": grant_status,
                    "revoke_status": None,
                    "ok": False,
                    "error": f"Grant failed: {grant_response.text}"
                })
                continue
                
            # Revoke permission
            revoke_response = requests.post(f"{BASE_URL}/api/admin/permissions/revoke",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={
                    "target_user_id": user_id,
                    "domain": domain,
                    "action": action,
                    "reason": f"P1.1 test revoke for {user_email} - domain={domain} action={action}"
                }
            )
            revoke_status = revoke_response.status_code
            revoke_ok = revoke_status == 200
            
            results.append({
                "user_email": user_email,
                "role": user_role,
                "domain": domain,
                "action": action,
                "grant_status": grant_status,
                "revoke_status": revoke_status,
                "ok": grant_ok and revoke_ok
            })
            
            print(f"User {idx+1}/{len(sample_users)}: {user_email} ({user_role}) - {domain}:{action} - Grant: {grant_status}, Revoke: {revoke_status}")
            
        # Assert all tests passed
        failed = [r for r in results if not r["ok"]]
        assert len(failed) == 0, f"Grant/Revoke failed for: {failed}"
        print(f"PASS: All {len(results)} grant/revoke operations succeeded")


class TestReasonValidation:
    """Test reason minimum 10 characters validation"""
    
    def test_grant_reason_too_short(self, admin_token):
        """Grant with reason < 10 chars returns 400"""
        # Get a non-super_admin user
        users_response = requests.get(f"{BASE_URL}/api/admin/permissions/users?limit=10", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert users_response.status_code == 200
        users = users_response.json().get("items", [])
        
        target_user = None
        for user in users:
            if user.get("role") != "super_admin":
                target_user = user
                break
                
        if not target_user:
            pytest.skip("No non-super_admin user found for testing")
            
        # Try grant with short reason
        response = requests.post(f"{BASE_URL}/api/admin/permissions/grant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": target_user["id"],
                "domain": "finance",
                "action": "view",
                "country_scope": [],
                "reason": "short"  # Less than 10 chars
            }
        )
        assert response.status_code in [400, 422], f"Expected 400 or 422 for short reason, got {response.status_code}"
        print("PASS: Short reason (< 10 chars) rejected with 400/422")
        
    def test_revoke_reason_too_short(self, admin_token):
        """Revoke with reason < 10 chars returns 400"""
        # Get a non-super_admin user
        users_response = requests.get(f"{BASE_URL}/api/admin/permissions/users?limit=10", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert users_response.status_code == 200
        users = users_response.json().get("items", [])
        
        target_user = None
        for user in users:
            if user.get("role") != "super_admin":
                target_user = user
                break
                
        if not target_user:
            pytest.skip("No non-super_admin user found for testing")
            
        # Try revoke with short reason
        response = requests.post(f"{BASE_URL}/api/admin/permissions/revoke",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": target_user["id"],
                "domain": "finance",
                "action": "view",
                "reason": "test"  # Less than 10 chars
            }
        )
        assert response.status_code in [400, 422], f"Expected 400 or 422 for short reason, got {response.status_code}"
        print("PASS: Short reason (< 10 chars) rejected with 400/422")


class TestAuditLinkage:
    """Test audit logs are created after permission mutations"""
    
    def test_audit_log_after_grant(self, admin_token):
        """Audit log entry is created after grant operation"""
        # Get a non-super_admin user
        users_response = requests.get(f"{BASE_URL}/api/admin/permissions/users?limit=10", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert users_response.status_code == 200
        users = users_response.json().get("items", [])
        
        target_user = None
        for user in users:
            if user.get("role") != "super_admin":
                target_user = user
                break
                
        if not target_user:
            pytest.skip("No non-super_admin user found for testing")
            
        # Perform grant
        grant_response = requests.post(f"{BASE_URL}/api/admin/permissions/grant",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": target_user["id"],
                "domain": "content",
                "action": "delete",
                "country_scope": [],
                "reason": f"Audit test grant for {target_user['email']}"
            }
        )
        assert grant_response.status_code == 200, f"Grant failed: {grant_response.text}"
        
        # Check audit logs
        audit_response = requests.get(f"{BASE_URL}/api/admin/audit-logs?action=PERMISSION_FLAG_GRANT&limit=10", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert audit_response.status_code == 200, f"Audit logs fetch failed: {audit_response.text}"
        audit_data = audit_response.json()
        
        # Verify audit entry exists
        found_entry = False
        for entry in audit_data.get("items", []):
            if entry.get("action") == "PERMISSION_FLAG_GRANT":
                found_entry = True
                break
                
        assert found_entry, "No PERMISSION_FLAG_GRANT audit entry found"
        print("PASS: Audit log entry created after grant")
        
        # Clean up - revoke the permission
        requests.post(f"{BASE_URL}/api/admin/permissions/revoke",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "target_user_id": target_user["id"],
                "domain": "content",
                "action": "delete",
                "reason": f"Audit test cleanup revoke for {target_user['email']}"
            }
        )


class TestShadowDiff:
    """Test shadow diff endpoint"""
    
    def test_shadow_diff_is_zero(self, admin_token):
        """Shadow diff count should be 0 (acceptance criteria)"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/shadow-diff", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Shadow diff failed: {response.text}"
        data = response.json()
        
        assert data["diff_count"] == 0, f"Shadow diff count is not 0: {data['diff_count']}, diffs: {data.get('diffs', [])}"
        print(f"PASS: Shadow diff = 0 (checked {data['checked_user_count']} users)")
        
    def test_shadow_diff_with_filters(self, admin_token):
        """Shadow diff works with role filter"""
        response = requests.get(f"{BASE_URL}/api/admin/permissions/shadow-diff?role=dealer", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200, f"Shadow diff with filter failed: {response.text}"
        data = response.json()
        assert "diff_count" in data
        assert "checked_user_count" in data
        print(f"PASS: Shadow diff with role filter returned diff_count={data['diff_count']}, checked={data['checked_user_count']}")
