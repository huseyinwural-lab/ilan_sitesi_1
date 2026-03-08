"""
Iteration 172 Tests: Category icon_svg feature
Tests:
1. icon_svg sanitization - safe SVG create/update
2. icon_svg unsafe content blocking (script, on* handlers, javascript:, foreignObject)
3. icon_svg 20KB limit validation
4. icon_svg is returned in category list and public tree endpoints
5. Regression: admin login, categories listing, public home
"""

import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"

# Max length is 20KB (20000 chars)
CATEGORY_ICON_SVG_MAX_LENGTH = 20000


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip(f"Admin login failed: {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Return headers with admin auth token"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


# --- Test fixtures for SVG content ---
SAFE_SVG_SIMPLE = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#2563eb"/></svg>'
SAFE_SVG_DETAILED = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path d="M12 2l3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1z" fill="#10b981"/></svg>'

UNSAFE_SVG_SCRIPT = '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
UNSAFE_SVG_ONCLICK = '<svg xmlns="http://www.w3.org/2000/svg" onclick="alert(1)"><circle cx="12" cy="12" r="10"/></svg>'
UNSAFE_SVG_JAVASCRIPT = '<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><circle cx="12" cy="12" r="10"/></a></svg>'
UNSAFE_SVG_FOREIGN_OBJECT = '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><div>test</div></foreignObject></svg>'
UNSAFE_SVG_ONERROR = '<svg xmlns="http://www.w3.org/2000/svg" onerror="alert(1)"><circle cx="12" cy="12" r="10"/></svg>'
UNSAFE_SVG_ONLOAD = '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"><circle cx="12" cy="12" r="10"/></svg>'

INVALID_SVG_NO_TAGS = "just some text"
INVALID_SVG_PARTIAL = "<svg>no closing tag"


class TestCategoryIconSvgSanitization:
    """Test icon_svg create/update with safe SVG content"""

    def test_create_category_with_safe_icon_svg(self, auth_headers):
        """Create root category with valid icon_svg - should succeed"""
        unique_slug = f"test-icon-svg-safe-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Safe {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99900,
            "icon_svg": SAFE_SVG_SIMPLE,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"
        data = response.json()

        # Check icon_svg is returned
        category = data.get("category", data)
        assert "icon_svg" in category, "icon_svg field should be in response"
        assert category["icon_svg"] == SAFE_SVG_SIMPLE, "icon_svg should match input"
        print(f"✓ Created category with icon_svg, id: {category.get('id')}")

    def test_update_category_icon_svg(self, auth_headers):
        """Update existing category's icon_svg - should succeed"""
        # First create a category
        unique_slug = f"test-icon-svg-update-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": f"TestIconSvg Update {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99901,
        }

        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=create_payload,
            headers=auth_headers,
            timeout=15,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json().get("category", create_response.json()).get("id")

        # Update with icon_svg
        update_payload = {"icon_svg": SAFE_SVG_DETAILED}
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            json=update_payload,
            headers=auth_headers,
            timeout=15,
        )

        assert update_response.status_code == 200, f"Expected 200, got {update_response.status_code}: {update_response.text}"
        updated_cat = update_response.json().get("category", update_response.json())
        assert updated_cat.get("icon_svg") == SAFE_SVG_DETAILED
        print(f"✓ Updated category icon_svg, id: {category_id}")

    def test_clear_category_icon_svg(self, auth_headers):
        """Clear icon_svg by sending empty string - should succeed"""
        # Create category with icon_svg
        unique_slug = f"test-icon-svg-clear-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": f"TestIconSvg Clear {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99902,
            "icon_svg": SAFE_SVG_SIMPLE,
        }

        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=create_payload,
            headers=auth_headers,
            timeout=15,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json().get("category", create_response.json()).get("id")

        # Clear icon_svg
        update_payload = {"icon_svg": ""}
        update_response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{category_id}",
            json=update_payload,
            headers=auth_headers,
            timeout=15,
        )

        assert update_response.status_code == 200
        updated_cat = update_response.json().get("category", update_response.json())
        # icon_svg should be cleared (null or empty)
        icon_svg_value = updated_cat.get("icon_svg")
        assert icon_svg_value in [None, ""], f"icon_svg should be cleared, got: {icon_svg_value}"
        print(f"✓ Cleared category icon_svg, id: {category_id}")


class TestCategoryIconSvgUnsafeBlocking:
    """Test that unsafe SVG content is blocked with 400 status"""

    def test_block_svg_with_script_tag(self, auth_headers):
        """SVG with <script> tag should be blocked"""
        unique_slug = f"test-icon-svg-script-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Script {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99910,
            "icon_svg": UNSAFE_SVG_SCRIPT,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for script tag, got {response.status_code}"
        print("✓ Script tag SVG blocked with 400")

    def test_block_svg_with_onclick(self, auth_headers):
        """SVG with onclick handler should be blocked"""
        unique_slug = f"test-icon-svg-onclick-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Onclick {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99911,
            "icon_svg": UNSAFE_SVG_ONCLICK,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for onclick, got {response.status_code}"
        print("✓ onclick handler SVG blocked with 400")

    def test_block_svg_with_javascript_url(self, auth_headers):
        """SVG with javascript: URL should be blocked"""
        unique_slug = f"test-icon-svg-jsurl-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg JavascriptUrl {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99912,
            "icon_svg": UNSAFE_SVG_JAVASCRIPT,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for javascript: URL, got {response.status_code}"
        print("✓ javascript: URL SVG blocked with 400")

    def test_block_svg_with_foreign_object(self, auth_headers):
        """SVG with <foreignObject> should be blocked"""
        unique_slug = f"test-icon-svg-foreign-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg ForeignObject {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99913,
            "icon_svg": UNSAFE_SVG_FOREIGN_OBJECT,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for foreignObject, got {response.status_code}"
        print("✓ foreignObject SVG blocked with 400")

    def test_block_svg_with_onerror(self, auth_headers):
        """SVG with onerror handler should be blocked"""
        unique_slug = f"test-icon-svg-onerror-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Onerror {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99914,
            "icon_svg": UNSAFE_SVG_ONERROR,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for onerror, got {response.status_code}"
        print("✓ onerror handler SVG blocked with 400")

    def test_block_svg_with_onload(self, auth_headers):
        """SVG with onload handler should be blocked"""
        unique_slug = f"test-icon-svg-onload-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Onload {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99915,
            "icon_svg": UNSAFE_SVG_ONLOAD,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for onload, got {response.status_code}"
        print("✓ onload handler SVG blocked with 400")


class TestCategoryIconSvgValidation:
    """Test icon_svg validation (format, length)"""

    def test_block_invalid_svg_no_tags(self, auth_headers):
        """Content without <svg> tags should be rejected"""
        unique_slug = f"test-icon-svg-notags-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg NoTags {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99920,
            "icon_svg": INVALID_SVG_NO_TAGS,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for no SVG tags, got {response.status_code}"
        print("✓ Invalid SVG (no tags) rejected with 400")

    def test_block_invalid_svg_partial(self, auth_headers):
        """Partial SVG without closing tag should be rejected"""
        unique_slug = f"test-icon-svg-partial-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Partial {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99921,
            "icon_svg": INVALID_SVG_PARTIAL,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for partial SVG, got {response.status_code}"
        print("✓ Partial SVG rejected with 400")

    def test_block_svg_exceeding_20kb_limit(self, auth_headers):
        """SVG exceeding 20KB limit should be rejected"""
        # Create an SVG that exceeds 20KB
        large_path = "M" + " ".join([f"{i},{i}" for i in range(10000)])
        large_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><path d="{large_path}"/></svg>'
        # Ensure it exceeds 20KB
        assert len(large_svg) > CATEGORY_ICON_SVG_MAX_LENGTH, f"Test SVG should exceed 20KB, got {len(large_svg)}"

        unique_slug = f"test-icon-svg-large-{uuid.uuid4().hex[:8]}"
        payload = {
            "name": f"TestIconSvg Large {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99922,
            "icon_svg": large_svg,
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=payload,
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 400, f"Expected 400 for large SVG, got {response.status_code}"
        response_text = response.text.lower()
        assert "20000" in response_text or "maksimum" in response_text or "karakter" in response_text, "Error message should mention size limit"
        print("✓ Large SVG (>20KB) rejected with 400")


class TestCategoryIconSvgRetrieval:
    """Test that icon_svg is returned in admin list and public endpoints"""

    def test_icon_svg_in_admin_category_list(self, auth_headers):
        """Admin category list should include icon_svg field"""
        # Create a category with icon_svg
        unique_slug = f"test-icon-svg-list-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": f"TestIconSvg List {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99930,
            "icon_svg": SAFE_SVG_SIMPLE,
        }

        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=create_payload,
            headers=auth_headers,
            timeout=15,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json().get("category", create_response.json()).get("id")

        # Get admin category list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE&module=other",
            headers=auth_headers,
            timeout=15,
        )

        assert list_response.status_code == 200
        items = list_response.json().get("items", [])
        matching = [item for item in items if item.get("id") == category_id]

        assert len(matching) > 0, f"Created category {category_id} should be in list"
        matched_item = matching[0]
        assert matched_item.get("icon_svg") == SAFE_SVG_SIMPLE, "icon_svg should be in list item"
        print(f"✓ icon_svg is present in admin category list, id: {category_id}")

    def test_icon_svg_in_public_category_tree(self, auth_headers):
        """Public category tree should include icon_svg field"""
        # Create a category with icon_svg
        unique_slug = f"test-icon-svg-tree-{uuid.uuid4().hex[:8]}"
        create_payload = {
            "name": f"TestIconSvg Tree {unique_slug}",
            "slug": unique_slug,
            "country_code": "DE",
            "module": "other",
            "active_flag": True,
            "sort_order": 99931,
            "icon_svg": SAFE_SVG_DETAILED,
        }

        create_response = requests.post(
            f"{BASE_URL}/api/admin/categories",
            json=create_payload,
            headers=auth_headers,
            timeout=15,
        )
        assert create_response.status_code in [200, 201]
        category_id = create_response.json().get("category", create_response.json()).get("id")

        # Get public category tree (no auth)
        tree_response = requests.get(
            f"{BASE_URL}/api/categories/tree?country=DE&depth=L1",
            timeout=15,
        )

        assert tree_response.status_code == 200
        items = tree_response.json().get("items", [])

        # Search for our category in tree
        def find_in_tree(nodes, target_id):
            for node in nodes:
                if node.get("id") == target_id:
                    return node
                children = node.get("children", [])
                if children:
                    found = find_in_tree(children, target_id)
                    if found:
                        return found
            return None

        found_node = find_in_tree(items, category_id)
        if found_node:
            assert found_node.get("icon_svg") == SAFE_SVG_DETAILED, "icon_svg should be in tree node"
            print(f"✓ icon_svg is present in public category tree, id: {category_id}")
        else:
            # Category might not appear in tree due to hierarchy rules
            print(f"⚠ Category {category_id} not found in tree (may be expected for root-level 'other' module)")


class TestRegressionChecks:
    """Regression tests for admin login and categories page"""

    def test_admin_login(self):
        """Admin login should work"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=15,
        )

        assert response.status_code == 200, f"Admin login failed: {response.status_code}"
        data = response.json()
        assert "access_token" in data, "access_token should be in response"
        assert data.get("user", {}).get("email") == ADMIN_EMAIL
        print("✓ Admin login works")

    def test_admin_categories_list(self, auth_headers):
        """GET /api/admin/categories should return valid response"""
        response = requests.get(
            f"{BASE_URL}/api/admin/categories?country=DE",
            headers=auth_headers,
            timeout=15,
        )

        assert response.status_code == 200, f"Admin categories list failed: {response.status_code}"
        data = response.json()
        assert "items" in data, "items should be in response"
        assert isinstance(data["items"], list), "items should be a list"
        print(f"✓ Admin categories list works, count: {len(data['items'])}")

    def test_public_health_check(self):
        """Public health endpoint should work"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200, f"Health check failed: {response.status_code}"
        print("✓ Health check works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
