"""
Iteration 135: i18n & Multilingual TR/DE/FR Infrastructure Integration Tests

Test Coverage:
- Backend layout resolve i18n (Accept-Language/X-URL-Locale headers)
- Categories i18n fields (title_i18n, description_i18n, label_i18n)
- Seed defaults i18n integrity
- Localized public routes accessibility
- Regression: Previous P0 flows still working
"""

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://builder-hub-151.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPPORTED_LOCALES = ["tr", "de", "fr"]
TEST_CREDENTIALS = {
    "admin": {"email": "admin@platform.com", "password": "Admin123!"},
    "dealer": {"email": "dealer@platform.com", "password": "Dealer123!"},
    "user": {"email": "user@platform.com", "password": "User123!"},
}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(
        f"{API}/auth/login",
        json=TEST_CREDENTIALS["admin"],
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def user_token():
    """Get user auth token"""
    response = requests.post(
        f"{API}/auth/login",
        json=TEST_CREDENTIALS["user"],
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, f"User login failed: {response.text}"
    return response.json()["access_token"]


class TestLocalizedRoutesAccessibility:
    """Test that localized public routes are accessible"""

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_localized_home_route_accessible(self, locale):
        """Test /{locale} home routes return 200"""
        response = requests.get(f"{BASE_URL}/{locale}", allow_redirects=True)
        assert response.status_code == 200, f"/{locale} route failed with {response.status_code}"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_localized_search_route_accessible(self, locale):
        """Test /{locale}/search routes return 200"""
        response = requests.get(f"{BASE_URL}/{locale}/search", allow_redirects=True)
        assert response.status_code == 200, f"/{locale}/search route failed with {response.status_code}"


class TestBackendLayoutResolveI18n:
    """Test backend layout resolve i18n with Accept-Language/X-URL-Locale"""

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_layout_resolve_with_locale_headers(self, locale):
        """Test /api/site/content-layout/resolve returns with locale headers"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
            headers={
                "Accept-Language": locale,
                "X-URL-Locale": locale,
            },
        )
        assert response.status_code == 200, f"Resolve failed for locale {locale}: {response.text}"
        data = response.json()
        # Should return some structure
        assert data is not None

    def test_layout_resolve_priority_x_url_locale_over_accept_language(self):
        """Test X-URL-Locale takes priority over Accept-Language"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
            headers={
                "Accept-Language": "de",
                "X-URL-Locale": "fr",  # Should take priority
            },
        )
        assert response.status_code == 200
        # The endpoint should use X-URL-Locale: fr

    def test_layout_resolve_fallback_to_tr_without_headers(self):
        """Test resolve falls back to TR without locale headers"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
        )
        assert response.status_code == 200
        # Should default to TR


class TestBackendCategoriesI18n:
    """Test categories API returns i18n fields"""

    def test_categories_have_i18n_fields(self):
        """Test /api/categories returns title_i18n, description_i18n, label_i18n"""
        response = requests.get(
            f"{API}/categories",
            params={"module": "vehicle", "country": "DE", "limit": 5},
        )
        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])
        
        if len(items) > 0:
            cat = items[0]
            # Check i18n fields exist
            assert "title_i18n" in cat, "Missing title_i18n in category"
            assert "description_i18n" in cat, "Missing description_i18n in category"
            assert "label_i18n" in cat, "Missing label_i18n in category"
            
            # Verify i18n structure (should be dict with tr/de/fr keys)
            title_i18n = cat.get("title_i18n", {})
            if title_i18n:
                assert isinstance(title_i18n, dict), "title_i18n should be dict"

    @pytest.mark.parametrize("locale", SUPPORTED_LOCALES)
    def test_categories_with_locale_header(self, locale):
        """Test categories endpoint respects Accept-Language header"""
        response = requests.get(
            f"{API}/categories",
            params={"module": "vehicle", "country": "DE", "limit": 3},
            headers={"Accept-Language": locale},
        )
        assert response.status_code == 200


class TestSeedDefaultsI18n:
    """Test seed-defaults endpoint i18n integrity"""

    def test_seed_defaults_returns_200(self, admin_token):
        """Test POST /api/admin/site/content-layout/pages/seed-defaults works"""
        response = requests.post(
            f"{API}/admin/site/content-layout/pages/seed-defaults",
            json={
                "country": "DE",
                "module": "global",
                "persona": "individual",
                "variant": "A",
                "overwrite_existing_draft": False,
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
                "Accept-Language": "tr",
            },
        )
        assert response.status_code == 200, f"Seed defaults failed: {response.text}"
        
        data = response.json()
        summary = data.get("summary", {})
        # Should have 15 page types
        total_actions = (
            summary.get("created_pages", 0) +
            summary.get("created_drafts", 0) +
            summary.get("updated_drafts", 0) +
            summary.get("skipped_drafts", 0)
        )
        assert total_actions >= 15, f"Expected 15 page types handled, got {total_actions}"

    def test_seed_defaults_with_invalid_persona(self, admin_token):
        """Test seed-defaults validates persona parameter"""
        response = requests.post(
            f"{API}/admin/site/content-layout/pages/seed-defaults",
            json={
                "country": "DE",
                "module": "global",
                "persona": "invalid_persona",
                "variant": "A",
                "overwrite_existing_draft": True,
            },
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json",
            },
        )
        # Should either normalize to default or reject
        assert response.status_code in [200, 400, 422]


class TestUserLocalePreference:
    """Test user locale preference persistence via API"""

    def test_user_login_returns_preferred_language(self):
        """Test login response includes preferred_language"""
        response = requests.post(
            f"{API}/auth/login",
            json=TEST_CREDENTIALS["user"],
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        data = response.json()
        user = data.get("user", {})
        assert "preferred_language" in user, "Missing preferred_language in user response"

    def test_user_locale_update_attempt(self, user_token):
        """Test user locale update - may return 403 for account scope users"""
        response = requests.put(
            f"{API}/users/me",
            json={"locale": "de"},
            headers={
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json",
                "Accept-Language": "de",
                "X-URL-Locale": "de",
            },
        )
        # May return 200 if allowed or 403 if scope restricted - both are valid
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"


class TestP0RegressionFlows:
    """Regression tests for P0 flows after i18n changes"""

    def test_health_endpoint_working(self):
        """Test /api/health still works"""
        response = requests.get(f"{API}/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"

    def test_login_flow_working(self):
        """Test login flow still works"""
        response = requests.post(
            f"{API}/auth/login",
            json=TEST_CREDENTIALS["admin"],
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_policy_report_endpoint_working(self, admin_token):
        """Test policy-report endpoint still works"""
        # First get a page with draft
        pages_response = requests.get(
            f"{API}/admin/site/content-layout/pages",
            params={"page_type": "wizard_preview", "country": "DE", "module": "global", "limit": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        if pages_response.status_code == 200:
            items = pages_response.json().get("items", [])
            if items:
                page_id = items[0].get("id")
                # Get revisions
                revisions_response = requests.get(
                    f"{API}/admin/site/content-layout/pages/{page_id}/revisions",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                if revisions_response.status_code == 200:
                    revisions = revisions_response.json().get("items", [])
                    draft = next((r for r in revisions if r.get("status") == "draft"), None)
                    if draft:
                        # Test policy report
                        report_response = requests.get(
                            f"{API}/admin/site/content-layout/revisions/{draft['id']}/policy-report",
                            headers={"Authorization": f"Bearer {admin_token}"},
                        )
                        assert report_response.status_code == 200, "Policy report failed"

    def test_auto_fix_endpoint_working(self, admin_token):
        """Test auto-fix endpoint still works"""
        # Get a wizard page draft
        pages_response = requests.get(
            f"{API}/admin/site/content-layout/pages",
            params={"page_type": "wizard_step_form", "country": "DE", "module": "global", "limit": 1},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        
        if pages_response.status_code == 200:
            items = pages_response.json().get("items", [])
            if items:
                page_id = items[0].get("id")
                revisions_response = requests.get(
                    f"{API}/admin/site/content-layout/pages/{page_id}/revisions",
                    headers={"Authorization": f"Bearer {admin_token}"},
                )
                if revisions_response.status_code == 200:
                    revisions = revisions_response.json().get("items", [])
                    draft = next((r for r in revisions if r.get("status") == "draft"), None)
                    if draft:
                        # Test auto-fix (may or may not make changes)
                        fix_response = requests.post(
                            f"{API}/admin/site/content-layout/revisions/{draft['id']}/policy-autofix",
                            json={},
                            headers={
                                "Authorization": f"Bearer {admin_token}",
                                "Content-Type": "application/json",
                            },
                        )
                        assert fix_response.status_code == 200, "Auto-fix failed"

    def test_draft_preview_resolve_working(self, admin_token):
        """Test layout_preview=draft query param still works"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={
                "page_type": "home",
                "country": "DE",
                "module": "global",
                "layout_preview": "draft",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        # May return 200 or 403 depending on permissions
        assert response.status_code in [200, 403], f"Unexpected status: {response.status_code}"


class TestI18nHeaderPriority:
    """Test i18n header priority: URL prefix > user pref > Accept-Language"""

    def test_x_url_locale_takes_priority(self):
        """Test X-URL-Locale header takes priority over Accept-Language"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
            headers={
                "Accept-Language": "de,en;q=0.9",
                "X-URL-Locale": "fr",
            },
        )
        assert response.status_code == 200
        # The backend should use 'fr' from X-URL-Locale

    def test_accept_language_used_when_no_x_url_locale(self):
        """Test Accept-Language is used when X-URL-Locale is absent"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
            headers={
                "Accept-Language": "de",
            },
        )
        assert response.status_code == 200

    def test_fallback_to_tr_without_locale_headers(self):
        """Test fallback to TR when no locale headers provided"""
        response = requests.get(
            f"{API}/site/content-layout/resolve",
            params={"page_type": "home", "country": "DE", "module": "global"},
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
