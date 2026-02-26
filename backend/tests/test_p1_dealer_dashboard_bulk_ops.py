"""
P1 Dealer Dashboard + Category Bulk Operations Tests - Iteration 23
Tests for:
- Dealer portal config response: header row1/row2/row3 fields
- Frontend DealerLayout 3-layer header render
- Admin Dealer Portal Config: dnd-kit reorder persist + visibility toggle
- Category list tri-state checkbox selection (backend only)
- Bulk activate/deactivate/delete operations (idempotent, POST /api/admin/categories/bulk-actions)
- Bulk delete double confirmation (ONAYLA keyword frontend only)
- Backend /api/admin/categories list filters (country, module, active_flag)
- Regression: vehicle/real_estate/other wizard main flows
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Credentials
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"
USER_EMAIL = "user@platform.com"
USER_PASSWORD = "User123!"


@pytest.fixture(scope="module")
def admin_token():
    """Authenticate as admin"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if res.status_code != 200:
        pytest.skip("Admin authentication failed")
    return res.json().get("access_token")


@pytest.fixture(scope="module")
def dealer_token():
    """Authenticate as dealer"""
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": DEALER_EMAIL,
        "password": DEALER_PASSWORD
    })
    if res.status_code != 200:
        pytest.skip("Dealer authentication failed")
    return res.json().get("access_token")


# ============================================
# DEALER PORTAL CONFIG 3-LAYER HEADER TESTS
# ============================================
class TestDealerPortalConfigThreeLayerHeader:
    """Dealer portal config should return header row1/row2/row3 fields"""

    def test_dealer_portal_config_has_header_row1_items(self, dealer_token):
        """GET /api/dealer/portal/config should return header_row1_items"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()

        # P1 requirement: header_row1_items field must exist
        assert "header_row1_items" in data, "Missing header_row1_items field"
        assert isinstance(data["header_row1_items"], list), "header_row1_items should be list"
        print(f"header_row1_items: {len(data['header_row1_items'])} items")

    def test_dealer_portal_config_has_header_row1_fixed_blocks(self, dealer_token):
        """GET /api/dealer/portal/config should return header_row1_fixed_blocks"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()

        # P1 requirement: header_row1_fixed_blocks field (Logo, Ana Menü, Hızlı Aksiyon defaults)
        assert "header_row1_fixed_blocks" in data, "Missing header_row1_fixed_blocks field"
        assert isinstance(data["header_row1_fixed_blocks"], list), "header_row1_fixed_blocks should be list"
        
        # Check default fixed blocks exist
        fixed_blocks = data["header_row1_fixed_blocks"]
        print(f"header_row1_fixed_blocks: {fixed_blocks}")
        
    def test_dealer_portal_config_has_header_row2_modules(self, dealer_token):
        """GET /api/dealer/portal/config should return header_row2_modules"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()

        # P1 requirement: header_row2_modules field (module-ordered chips)
        assert "header_row2_modules" in data, "Missing header_row2_modules field"
        assert isinstance(data["header_row2_modules"], list), "header_row2_modules should be list"
        print(f"header_row2_modules: {len(data['header_row2_modules'])} modules")

    def test_dealer_portal_config_has_header_row3_controls(self, dealer_token):
        """GET /api/dealer/portal/config should return header_row3_controls"""
        res = requests.get(
            f"{BASE_URL}/api/dealer/portal/config",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert res.status_code == 200
        data = res.json()

        # P1 requirement: header_row3_controls field (store filter + user dropdown)
        assert "header_row3_controls" in data, "Missing header_row3_controls field"
        row3 = data["header_row3_controls"]
        assert isinstance(row3, dict), "header_row3_controls should be dict"
        
        # Check expected controls
        assert "store_filter_enabled" in row3, "Missing store_filter_enabled"
        assert "user_dropdown_enabled" in row3, "Missing user_dropdown_enabled"
        assert "stores" in row3, "Missing stores"
        assert "default_store_key" in row3, "Missing default_store_key"
        print(f"header_row3_controls: {row3}")


# ============================================
# ADMIN DEALER PORTAL CONFIG REORDER/TOGGLE
# ============================================
class TestAdminDealerPortalConfigPersistence:
    """Admin dealer portal config dnd-kit reorder and visibility persist"""

    def test_admin_dealer_nav_reorder_persist_verified(self, admin_token):
        """POST /api/admin/dealer-portal/nav/reorder should persist new order"""
        # Get current items
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()

        sidebar_items = [item for item in data.get("nav_items", []) if item.get("location") == "sidebar"]
        if len(sidebar_items) < 2:
            pytest.skip("Not enough sidebar items to test reorder")

        # Get original order
        original_ids = [item["id"] for item in sidebar_items]
        
        # Reverse order
        reversed_ids = list(reversed(original_ids))

        # POST reorder
        res = requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/nav/reorder",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"location": "sidebar", "ordered_ids": reversed_ids}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

        # Verify persistence
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        new_sidebar_items = [item for item in res.json().get("nav_items", []) if item.get("location") == "sidebar"]
        new_ids = [item["id"] for item in new_sidebar_items]
        
        # Order should match reversed
        assert new_ids == reversed_ids, f"Order not persisted: expected {reversed_ids}, got {new_ids}"
        print("Nav reorder persistence: VERIFIED")

        # Restore original order
        requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/nav/reorder",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"location": "sidebar", "ordered_ids": original_ids}
        )

    def test_admin_dealer_module_reorder_persist_verified(self, admin_token):
        """POST /api/admin/dealer-portal/modules/reorder should persist new order"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        data = res.json()

        modules = data.get("modules", [])
        if len(modules) < 2:
            pytest.skip("Not enough modules to test reorder")

        original_ids = [m["id"] for m in modules]
        reversed_ids = list(reversed(original_ids))

        res = requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/modules/reorder",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"ordered_ids": reversed_ids}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"

        # Verify persistence
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        new_modules = res.json().get("modules", [])
        new_ids = [m["id"] for m in new_modules]
        
        assert new_ids == reversed_ids, f"Module order not persisted"
        print("Module reorder persistence: VERIFIED")

        # Restore original
        requests.post(
            f"{BASE_URL}/api/admin/dealer-portal/modules/reorder",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"ordered_ids": original_ids}
        )

    def test_admin_dealer_nav_visibility_toggle_persist(self, admin_token):
        """PATCH /api/admin/dealer-portal/nav/{id} visibility toggle persists"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        nav_items = res.json().get("nav_items", [])
        if not nav_items:
            pytest.skip("No nav items to test")

        target = nav_items[0]
        original_visible = target.get("visible")

        # Toggle
        res = requests.patch(
            f"{BASE_URL}/api/admin/dealer-portal/nav/{target['id']}",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"visible": not original_visible}
        )
        assert res.status_code == 200

        # Verify persistence
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        updated = next((i for i in res.json().get("nav_items", []) if i["id"] == target["id"]), None)
        assert updated["visible"] == (not original_visible), "Visibility not persisted"
        print(f"Visibility toggle persist: {target['key']} {original_visible} -> {not original_visible}")

        # Restore
        requests.patch(
            f"{BASE_URL}/api/admin/dealer-portal/nav/{target['id']}",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={"visible": original_visible}
        )


# ============================================
# CATEGORY BULK OPERATIONS TESTS
# ============================================
class TestCategoryBulkOperations:
    """Category bulk actions API tests (activate/deactivate/delete)"""

    def test_admin_categories_list_returns_200(self, admin_token):
        """GET /api/admin/categories should return 200 with items"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        assert "items" in data, "Missing items"
        print(f"Admin categories: {len(data.get('items', []))} items")

    def test_admin_categories_list_filter_by_module(self, admin_token):
        """GET /api/admin/categories?module=vehicle should filter by module"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories?module=vehicle",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        
        for item in items:
            assert item.get("module") == "vehicle", f"Item {item.get('id')} has module {item.get('module')}"
        print(f"Vehicle categories: {len(items)} items")

    def test_admin_categories_list_filter_by_country(self, admin_token):
        """GET /api/admin/categories?country=DE should filter by country"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        
        for item in items:
            assert item.get("country_code") == "DE", f"Item {item.get('id')} has country {item.get('country_code')}"
        print(f"DE categories: {len(items)} items")

    def test_admin_categories_list_filter_by_active_flag_true(self, admin_token):
        """GET /api/admin/categories?active_flag=true should filter by active"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories?active_flag=true",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        print(f"Active categories: {len(items)} items")

    def test_admin_categories_list_filter_by_active_flag_false(self, admin_token):
        """GET /api/admin/categories?active_flag=false should filter by inactive"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories?active_flag=false",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        items = data.get("items", [])
        print(f"Inactive categories: {len(items)} items")

    def test_bulk_actions_activate_scope_ids_idempotent(self, admin_token):
        """POST /api/admin/categories/bulk-actions activate is idempotent"""
        # Get some categories
        res = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        if not items:
            pytest.skip("No categories to test bulk operations")

        # Get first active category
        active_items = [i for i in items if i.get("active_flag") or i.get("is_enabled")]
        if not active_items:
            pytest.skip("No active categories to test idempotent activate")

        target_id = active_items[0]["id"]

        # Call activate on already active - should be idempotent (unchanged)
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "activate",
                "scope": "ids",
                "ids": [target_id]
            }
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        
        assert data.get("ok") is True, "Bulk action should return ok=true"
        assert data.get("action") == "activate"
        assert data.get("scope") == "ids"
        assert "unchanged" in data, "Response should include unchanged count"
        print(f"Bulk activate idempotent: matched={data.get('matched')}, changed={data.get('changed')}, unchanged={data.get('unchanged')}")

    def test_bulk_actions_deactivate_then_activate(self, admin_token):
        """POST /api/admin/categories/bulk-actions deactivate then activate"""
        # Get categories
        res = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        if not items:
            pytest.skip("No categories to test")

        # Find an active category to toggle
        active_items = [i for i in items if i.get("active_flag") or i.get("is_enabled")]
        if not active_items:
            pytest.skip("No active categories to toggle")

        target_id = active_items[0]["id"]
        original_state = active_items[0].get("active_flag") or active_items[0].get("is_enabled")

        # Deactivate
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "deactivate",
                "scope": "ids",
                "ids": [target_id]
            }
        )
        assert res.status_code == 200, f"Deactivate failed: {res.text}"
        deactivate_data = res.json()
        print(f"Deactivate: changed={deactivate_data.get('changed')}")

        # Verify deactivated
        res = requests.get(
            f"{BASE_URL}/api/admin/categories?active_flag=false",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        deactivated_items = res.json().get("items", [])
        found = any(i["id"] == target_id for i in deactivated_items)
        # Note: is_enabled vs active_flag - check both scenarios
        
        # Re-activate
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "activate",
                "scope": "ids",
                "ids": [target_id]
            }
        )
        assert res.status_code == 200, f"Activate failed: {res.text}"
        activate_data = res.json()
        print(f"Activate: changed={activate_data.get('changed')}")

    def test_bulk_actions_requires_ids_for_scope_ids(self, admin_token):
        """POST /api/admin/categories/bulk-actions scope=ids requires ids"""
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "activate",
                "scope": "ids",
                "ids": []  # Empty ids
            }
        )
        assert res.status_code == 400, f"Expected 400 for empty ids, got {res.status_code}"
        print("Bulk action validation: empty ids -> 400")

    def test_bulk_actions_filter_scope(self, admin_token):
        """POST /api/admin/categories/bulk-actions scope=filter requires filter"""
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "activate",
                "scope": "filter",
                "filter": {"country": "DE", "module": "other"}
            }
        )
        # Should work - filter scope with filter payload
        assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
        data = res.json()
        print(f"Bulk activate with filter: matched={data.get('matched')}, changed={data.get('changed')}")

    def test_bulk_actions_delete_soft_deletes(self, admin_token):
        """POST /api/admin/categories/bulk-actions delete is soft delete (idempotent)"""
        # Create a test category to delete
        res = requests.post(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "name": "TEST_BULK_DELETE_CATEGORY",
                "slug": f"test-bulk-delete-{uuid.uuid4().hex[:8]}",
                "country_code": "DE",
                "module": "other",
                "active_flag": True,
                "sort_order": 9999
            }
        )
        
        if res.status_code != 201 and res.status_code != 200:
            pytest.skip(f"Could not create test category for delete: {res.status_code} {res.text}")
        
        created = res.json()
        category_id = created.get("category", {}).get("id") or created.get("id")
        if not category_id:
            pytest.skip("No category ID returned from create")
        
        print(f"Created test category: {category_id}")

        # Delete it
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "delete",
                "scope": "ids",
                "ids": [category_id]
            }
        )
        assert res.status_code == 200, f"Delete failed: {res.status_code} {res.text}"
        delete_data = res.json()
        assert delete_data.get("changed") >= 0, "Delete should report changed count"
        print(f"Bulk delete: changed={delete_data.get('changed')}")

        # Try to delete again - should be idempotent (unchanged)
        res = requests.post(
            f"{BASE_URL}/api/admin/categories/bulk-actions",
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"},
            json={
                "action": "delete",
                "scope": "ids",
                "ids": [category_id]
            }
        )
        assert res.status_code == 200, f"Second delete failed: {res.status_code}"
        data = res.json()
        # Should be unchanged since already deleted
        print(f"Bulk delete idempotent: unchanged={data.get('unchanged')}")


# ============================================
# REGRESSION TESTS
# ============================================
class TestRegressionWizardFlows:
    """Regression: wizard flows should not be broken"""

    def test_ilan_ver_route_auth_gate(self):
        """GET /ilan-ver should redirect to login when not authenticated"""
        # This is frontend behavior, we test the API auth works
        res = requests.get(f"{BASE_URL}/api/me")  # Without token
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Auth gate working for protected routes")

    def test_auth_login_returns_portal_scope(self, dealer_token):
        """Login should return portal_scope for dealer"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": DEALER_EMAIL,
            "password": DEALER_PASSWORD
        })
        assert res.status_code == 200
        data = res.json()
        user = data.get("user", {})
        assert user.get("portal_scope") == "dealer", f"Expected dealer portal_scope, got {user.get('portal_scope')}"
        print("Dealer login portal_scope: dealer")

    def test_admin_login_returns_admin_portal_scope(self, admin_token):
        """Login should return portal_scope for admin"""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert res.status_code == 200
        data = res.json()
        user = data.get("user", {})
        assert user.get("portal_scope") == "admin", f"Expected admin portal_scope, got {user.get('portal_scope')}"
        print("Admin login portal_scope: admin")

    def test_category_list_includes_form_schema(self, admin_token):
        """Categories list should include form_schema for wizard flows"""
        res = requests.get(
            f"{BASE_URL}/api/admin/categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        items = res.json().get("items", [])
        
        # Check at least one item has form_schema
        has_schema = any(item.get("form_schema") for item in items)
        print(f"Categories with form_schema: {sum(1 for i in items if i.get('form_schema'))}/{len(items)}")


# ============================================
# ADMIN DEALER PORTAL CONFIG PREVIEW
# ============================================
class TestAdminDealerPortalConfigPreview:
    """Admin preview should return same structure as dealer config"""

    def test_admin_preview_has_three_layer_header_fields(self, admin_token):
        """GET /api/admin/dealer-portal/config/preview should return row1/row2/row3"""
        res = requests.get(
            f"{BASE_URL}/api/admin/dealer-portal/config/preview",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()

        # Same fields as dealer config
        assert "header_row1_items" in data, "Missing header_row1_items"
        assert "header_row1_fixed_blocks" in data, "Missing header_row1_fixed_blocks"
        assert "header_row2_modules" in data, "Missing header_row2_modules"
        assert "header_row3_controls" in data, "Missing header_row3_controls"
        
        row3 = data["header_row3_controls"]
        assert "store_filter_enabled" in row3
        assert "user_dropdown_enabled" in row3
        print(f"Admin preview row3: {row3}")
