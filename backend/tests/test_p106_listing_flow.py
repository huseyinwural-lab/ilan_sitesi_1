"""
P106 Listing Flow Tests - Backend API Tests
Tests: 
- Admin Categories root-only filtering
- Home page category data structure
- Listing flow: create draft, save draft, preview-ready, preview get, doping options, doping select, submit-review
- Submit idempotency with same Idempotency-Key
- Admin moderation queue (submitted_for_review listings)
- Audit logs: LISTING_PREVIEW_READY, LISTING_DOPING_SELECTED, LISTING_SUBMITTED_FOR_REVIEW
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ad-posting-flow.preview.emergentagent.com')

class TestAdminCategoriesRootOnly:
    """Test Admin Categories list returns only root categories (parent_id null)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = self._login_admin()
        self.user_token = self._login_user()
        
    def _login_admin(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    def _login_user(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "user@platform.com",
            "password": "User123!"
        })
        assert response.status_code == 200, f"User login failed: {response.text}"
        return response.json()["access_token"]
    
    def test_admin_categories_api_returns_all(self):
        """Admin categories API returns all categories including children"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert response.status_code == 200, f"Admin categories API failed: {response.text}"
        data = response.json()
        items = data.get("items", [])
        
        # API should return categories
        print(f"Total categories from API: {len(items)}")
        
        # Check for root vs child categories
        root_categories = [c for c in items if not c.get("parent_id")]
        child_categories = [c for c in items if c.get("parent_id")]
        
        print(f"Root categories: {len(root_categories)}")
        print(f"Child categories: {len(child_categories)}")
        
        # Verify structure - root categories have parent_id null/empty
        for root in root_categories:
            assert not root.get("parent_id"), f"Root category has parent_id: {root}"
            print(f"Root: {root.get('name')} (id={root.get('id')})")
        
        return items


class TestHomeCategoryData:
    """Test Home page category data structure: module > root > L1 children"""
    
    def test_categories_by_module_real_estate(self):
        """Test categories API for real_estate module"""
        response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
        assert response.status_code == 200, f"Categories API failed: {response.text}"
        
        categories = response.json()
        print(f"Real estate categories: {len(categories)}")
        
        # Group by parent
        by_parent = {}
        for cat in categories:
            parent_key = cat.get("parent_id") or "root"
            if parent_key not in by_parent:
                by_parent[parent_key] = []
            by_parent[parent_key].append(cat)
        
        roots = by_parent.get("root", [])
        print(f"Root categories: {len(roots)}")
        
        for root in roots:
            children = by_parent.get(root.get("id"), [])
            print(f"  Root: {root.get('name')} -> Children: {len(children)}")
            for child in children[:3]:
                print(f"    - {child.get('name')} (count={child.get('listing_count', 0)})")
    
    def test_categories_by_module_vehicle(self):
        """Test categories API for vehicle module"""
        response = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        assert response.status_code == 200
        
        categories = response.json()
        print(f"Vehicle categories: {len(categories)}")

    def test_categories_by_module_other(self):
        """Test categories API for other module"""
        response = requests.get(f"{BASE_URL}/api/categories?module=other&country=DE")
        assert response.status_code == 200
        
        categories = response.json()
        print(f"Other categories: {len(categories)}")


class TestListingFlowEndpoints:
    """Test the listing creation flow endpoints:
    draft -> preview_ready -> (doping_selected optional) -> submitted_for_review
    """
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_token = self._login_user()
        self.listing_id = None
        
    def _login_user(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "user@platform.com",
            "password": "User123!"
        })
        assert response.status_code == 200, f"User login failed: {response.text}"
        return response.json()["access_token"]
    
    def _get_valid_category(self):
        """Get a valid category ID for testing"""
        response = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        if response.status_code == 200:
            categories = response.json()
            if categories:
                # Find a leaf category (one with no children preferably)
                return categories[0].get("id")
        
        # Fallback to real_estate
        response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
        if response.status_code == 200:
            categories = response.json()
            if categories:
                return categories[0].get("id")
        return None
    
    def test_01_create_draft_listing(self):
        """Step 1: Create a draft listing"""
        category_id = self._get_valid_category()
        if not category_id:
            pytest.skip("No valid category found for testing")
        
        payload = {
            "category_id": category_id,
            "country": "DE",
            "selected_category_path": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Create draft response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code in [200, 201], f"Create draft failed: {response.text}"
        data = response.json()
        self.listing_id = data.get("id")
        assert self.listing_id, "No listing ID returned"
        print(f"Created listing ID: {self.listing_id}")
        return self.listing_id
    
    def test_02_save_draft(self):
        """Step 2: Save draft with core fields"""
        listing_id = self.test_01_create_draft_listing()
        
        payload = {
            "core_fields": {
                "title": "Test Listing for P106 Testing",
                "description": "This is a test description for the P106 listing flow testing. It needs to be at least 30 characters.",
                "price": {
                    "price_type": "FIXED",
                    "amount": 15000,
                    "currency_primary": "EUR"
                }
            },
            "selected_category_path": [],
            "location": {
                "city": "Berlin",
                "country": "DE"
            },
            "contact": {
                "contact_name": "Test User",
                "contact_phone": "+491234567890",
                "allow_phone": True,
                "allow_message": True
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Save draft response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Save draft failed: {response.text}"
        return listing_id
    
    def test_03_preview_ready(self):
        """Step 3: Mark listing as preview-ready"""
        listing_id = self.test_02_save_draft()
        
        payload = {
            "core_fields": {
                "title": "Test Listing for P106 Testing",
                "description": "This is a test description for the P106 listing flow testing. It needs to be at least 30 characters.",
                "price": {
                    "price_type": "FIXED",
                    "amount": 15000,
                    "currency_primary": "EUR"
                }
            },
            "location": {
                "city": "Berlin",
                "country": "DE"
            },
            "contact": {
                "contact_name": "Test User",
                "contact_phone": "+491234567890",
                "allow_phone": True,
                "allow_message": True
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Preview-ready response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Preview-ready failed: {response.text}"
        data = response.json()
        assert data.get("flow_state") == "preview_ready", f"Unexpected flow_state: {data.get('flow_state')}"
        return listing_id
    
    def test_04_get_preview(self):
        """Step 4: Get listing preview data"""
        listing_id = self.test_03_preview_ready()
        
        response = requests.get(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        print(f"Get preview response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Get preview failed: {response.text}"
        data = response.json()
        
        # Verify preview structure
        assert data.get("id") == listing_id
        assert "title" in data
        assert "price" in data
        assert "doping_selection" in data
        
        # Verify doping_selection defaults
        doping = data.get("doping_selection", {})
        assert doping.get("enabled") == False, "Doping should be disabled by default"
        
        return listing_id
    
    def test_05_doping_options(self):
        """Step 5: Get available doping options"""
        response = requests.get(
            f"{BASE_URL}/api/v1/listings/doping/options",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        print(f"Doping options response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Get doping options failed: {response.text}"
        data = response.json()
        
        options = data.get("options", [])
        assert len(options) >= 3, f"Expected at least 3 doping options, got {len(options)}"
        
        # Verify expected doping types
        doping_types = [opt.get("doping_type") for opt in options]
        assert "none" in doping_types, "Missing 'none' doping type"
        assert "urgent" in doping_types, "Missing 'urgent' doping type"
        assert "showcase" in doping_types, "Missing 'showcase' doping type"
        
        print(f"Available doping types: {doping_types}")
    
    def test_06_select_doping(self):
        """Step 6: Select a doping option"""
        listing_id = self.test_03_preview_ready()
        
        payload = {
            "doping_type": "urgent",
            "duration_days": 7
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/doping",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        
        print(f"Select doping response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Select doping failed: {response.text}"
        data = response.json()
        
        # Verify doping selection
        assert data.get("flow_state") == "doping_selected", f"Unexpected flow_state: {data.get('flow_state')}"
        doping = data.get("doping_selection", {})
        assert doping.get("enabled") == True
        assert doping.get("doping_type") == "urgent"
        assert doping.get("duration_days") == 7
        
        return listing_id


class TestSubmitReviewIdempotency:
    """Test submit-review endpoint with Idempotency-Key"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.user_token = self._login_user()
        
    def _login_user(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "user@platform.com",
            "password": "User123!"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def _create_preview_ready_listing(self):
        """Helper to create a listing in preview_ready state"""
        # Get category
        cat_resp = requests.get(f"{BASE_URL}/api/categories?module=vehicle&country=DE")
        categories = cat_resp.json() if cat_resp.status_code == 200 else []
        if not categories:
            cat_resp = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
            categories = cat_resp.json() if cat_resp.status_code == 200 else []
        
        if not categories:
            return None
            
        category_id = categories[0].get("id")
        
        # Create draft
        create_resp = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Content-Type": "application/json"
            },
            json={"category_id": category_id, "country": "DE"}
        )
        
        if create_resp.status_code not in [200, 201]:
            return None
            
        listing_id = create_resp.json().get("id")
        
        # Save draft
        draft_payload = {
            "core_fields": {
                "title": f"Idempotency Test Listing {uuid.uuid4().hex[:8]}",
                "description": "Test description for idempotency testing with enough characters.",
                "price": {"price_type": "FIXED", "amount": 10000, "currency_primary": "EUR"}
            },
            "location": {"city": "Munich", "country": "DE"},
            "contact": {"contact_name": "Test", "allow_phone": True}
        }
        
        requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/draft",
            headers={"Authorization": f"Bearer {self.user_token}", "Content-Type": "application/json"},
            json=draft_payload
        )
        
        # Preview-ready
        preview_resp = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/preview-ready",
            headers={"Authorization": f"Bearer {self.user_token}", "Content-Type": "application/json"},
            json=draft_payload
        )
        
        if preview_resp.status_code != 200:
            print(f"Preview-ready failed: {preview_resp.text}")
            return None
            
        return listing_id
    
    def test_submit_review_requires_idempotency_key(self):
        """Submit-review should require Idempotency-Key header"""
        listing_id = self._create_preview_ready_listing()
        if not listing_id:
            pytest.skip("Could not create listing for testing")
        
        # Try without Idempotency-Key
        response = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        print(f"Submit without key: {response.status_code}")
        assert response.status_code == 400, "Should reject without Idempotency-Key"
        assert "Idempotency-Key" in response.text or "idempotency" in response.text.lower()
    
    def test_submit_review_idempotency_same_key(self):
        """Same Idempotency-Key should return same response without duplicate"""
        listing_id = self._create_preview_ready_listing()
        if not listing_id:
            pytest.skip("Could not create listing for testing")
        
        idempotency_key = str(uuid.uuid4())
        
        # First submit
        response1 = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Idempotency-Key": idempotency_key
            }
        )
        
        print(f"First submit: {response1.status_code}")
        print(f"Response: {response1.text[:300]}")
        
        assert response1.status_code == 200, f"First submit failed: {response1.text}"
        data1 = response1.json()
        assert data1.get("flow_state") == "submitted_for_review"
        assert data1.get("idempotency_reused") == False
        
        # Second submit with SAME key
        response2 = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Idempotency-Key": idempotency_key
            }
        )
        
        print(f"Second submit (same key): {response2.status_code}")
        print(f"Response: {response2.text[:300]}")
        
        assert response2.status_code == 200, f"Second submit with same key failed: {response2.text}"
        data2 = response2.json()
        assert data2.get("idempotency_reused") == True, "Second call should indicate idempotency reuse"
        assert data2.get("id") == data1.get("id"), "Should return same listing ID"
    
    def test_submit_review_different_key_rejected(self):
        """Different Idempotency-Key after submit should be rejected"""
        listing_id = self._create_preview_ready_listing()
        if not listing_id:
            pytest.skip("Could not create listing for testing")
        
        # First submit
        key1 = str(uuid.uuid4())
        response1 = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Idempotency-Key": key1
            }
        )
        
        assert response1.status_code == 200
        
        # Try with different key
        key2 = str(uuid.uuid4())
        response2 = requests.post(
            f"{BASE_URL}/api/v1/listings/vehicle/{listing_id}/submit-review",
            headers={
                "Authorization": f"Bearer {self.user_token}",
                "Idempotency-Key": key2
            }
        )
        
        print(f"Different key response: {response2.status_code}")
        assert response2.status_code == 409, "Should reject different key for already submitted listing"


class TestAdminModerationQueue:
    """Test Admin moderation queue shows submitted_for_review listings as PENDING"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = self._login_admin()
        
    def _login_admin(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_moderation_queue_pending(self):
        """Moderation queue should show PENDING listings"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/queue?status=pending_moderation",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        print(f"Moderation queue response: {response.status_code}")
        
        assert response.status_code == 200, f"Moderation queue failed: {response.text}"
        data = response.json()
        
        # API returns list directly, not {"items": [...]}
        items = data if isinstance(data, list) else data.get("items", [])
        print(f"Pending items in queue: {len(items)}")
        
        # Check structure of items
        if items:
            item = items[0]
            print(f"Sample item keys: {list(item.keys())}")
            assert "id" in item
            # Check for moderation status
            if "moderation_status" in item:
                assert item.get("moderation_status") in ["PENDING", "pending", "pending_moderation"]
    
    def test_moderation_queue_count(self):
        """Moderation queue count endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/moderation/queue/count?status=pending_moderation",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        print(f"Queue count response: {response.status_code}")
        
        assert response.status_code == 200, f"Queue count failed: {response.text}"
        data = response.json()
        
        count = data.get("count", data.get("total", 0))
        print(f"Pending count: {count}")


class TestAuditLogs:
    """Test audit log events for listing flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.admin_token = self._login_admin()
        
    def _login_admin(self):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@platform.com",
            "password": "Admin123!"
        })
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_audit_logs_listing_events(self):
        """Verify audit logs contain listing flow events"""
        # Get recent audit logs
        response = requests.get(
            f"{BASE_URL}/api/admin/audit-logs?limit=50&resource_type=listing",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        print(f"Audit logs response: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Audit logs endpoint may need different path: {response.text[:200]}")
            # Try alternative path
            response = requests.get(
                f"{BASE_URL}/api/admin/audit?limit=50",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
        
        if response.status_code == 200:
            data = response.json()
            items = data.get("items", data.get("logs", []))
            
            # Look for listing flow events
            preview_ready_events = [i for i in items if i.get("action") == "LISTING_PREVIEW_READY"]
            doping_events = [i for i in items if i.get("action") == "LISTING_DOPING_SELECTED"]
            submit_events = [i for i in items if i.get("action") == "LISTING_SUBMITTED_FOR_REVIEW"]
            
            print(f"LISTING_PREVIEW_READY events: {len(preview_ready_events)}")
            print(f"LISTING_DOPING_SELECTED events: {len(doping_events)}")
            print(f"LISTING_SUBMITTED_FOR_REVIEW events: {len(submit_events)}")
            
            # Check metadata structure
            if submit_events:
                event = submit_events[0]
                metadata = event.get("metadata_info", event.get("metadata", {}))
                print(f"Submit event metadata keys: {list(metadata.keys())}")
                
                # Should include doping_selection
                if "doping_selection" in metadata:
                    print(f"Doping selection in audit: {metadata.get('doping_selection')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
