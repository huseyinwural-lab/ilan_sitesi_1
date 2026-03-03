"""
P1 Final Iteration Tests:
- Trust/Policy/Corporate/SEO public pages
- System templates (500, maintenance)
- Backend fallback content for info pages
- Admin finance standardization (subscriptions, invoices)
- User finance screens regression
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://monolith-modular-5.preview.emergentagent.com")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "admin@platform.com", "password": "Admin123!"},
    )
    if response.status_code != 200:
        pytest.skip("Admin login failed")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def user_token():
    """Get user auth token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "user@platform.com", "password": "User123!"},
    )
    if response.status_code != 200:
        pytest.skip("User login failed")
    return response.json().get("access_token")


class TestInfoPageFallbacks:
    """Test backend fallback content for info pages"""

    def test_gizlilik_politikasi_fallback(self):
        """Gizlilik Politikası returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/gizlilik-politikasi")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "gizlilik-politikasi"
        assert data.get("source") == "fallback"
        assert data.get("title_tr")
        assert data.get("content_tr")

    def test_cerez_politikasi_fallback(self):
        """Çerez Politikası returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/cerez-politikasi")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "cerez-politikasi"
        assert data.get("source") == "fallback"
        assert data.get("title_tr")

    def test_yardim_merkezi_fallback(self):
        """Yardım Merkezi returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/yardim-merkezi")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "yardim-merkezi"
        assert data.get("source") == "fallback"

    def test_site_haritasi_fallback(self):
        """Site Haritası returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/site-haritasi")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "site-haritasi"
        assert data.get("source") == "fallback"

    def test_kullanim_kosullari_fallback(self):
        """Kullanım Koşulları returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/kullanim-kosullari")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "kullanim-kosullari"
        assert data.get("source") == "fallback"

    def test_kvkk_aydinlatma_fallback(self):
        """KVKK Aydınlatma returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/kvkk-aydinlatma")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "kvkk-aydinlatma"
        assert data.get("source") == "fallback"

    def test_mesafeli_satis_sozlesmesi_fallback(self):
        """Mesafeli Satış Sözleşmesi returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/mesafeli-satis-sozlesmesi")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "mesafeli-satis-sozlesmesi"
        assert data.get("source") == "fallback"

    def test_hakkimizda_fallback(self):
        """Hakkımızda returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/hakkimizda")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "hakkimizda"
        assert data.get("source") == "fallback"

    def test_iletisim_fallback(self):
        """İletişim returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/iletisim")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "iletisim"
        assert data.get("source") == "fallback"

    def test_magaza_cozumleri_fallback(self):
        """Mağaza Çözümleri returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/magaza-cozumleri")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "magaza-cozumleri"
        assert data.get("source") == "fallback"

    def test_kurumsal_ilan_cozumleri_fallback(self):
        """Kurumsal İlan Çözümleri returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/kurumsal-ilan-cozumleri")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "kurumsal-ilan-cozumleri"
        assert data.get("source") == "fallback"

    def test_nasil_calisir_fallback(self):
        """Nasıl Çalışır? returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/nasil-calisir")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "nasil-calisir"
        assert data.get("source") == "fallback"

    def test_guvenli_alisveris_fallback(self):
        """Güvenli Alışveriş Rehberi returns 200 with fallback content"""
        response = requests.get(f"{BASE_URL}/api/info/guvenli-alisveris")
        assert response.status_code == 200
        data = response.json()
        assert data.get("slug") == "guvenli-alisveris"
        assert data.get("source") == "fallback"

    def test_nonexistent_slug_returns_404(self):
        """Non-existent slug returns 404"""
        response = requests.get(f"{BASE_URL}/api/info/nonexistent-page-slug")
        assert response.status_code == 404


class TestAdminFinanceSubscriptions:
    """Admin finance subscriptions endpoint tests"""

    def test_admin_subscriptions_list(self, admin_token):
        """GET /api/admin/finance/subscriptions returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/finance/subscriptions",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_admin_subscriptions_filter_by_status(self, admin_token):
        """GET /api/admin/finance/subscriptions with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/finance/subscriptions?status=active",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestAdminFinanceInvoices:
    """Admin finance invoices endpoint tests"""

    def test_admin_invoices_list(self, admin_token):
        """GET /api/admin/invoices with country filter returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices?country=DE",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "pagination" in data

    def test_admin_invoices_filter_by_status(self, admin_token):
        """GET /api/admin/invoices with status filter"""
        response = requests.get(
            f"{BASE_URL}/api/admin/invoices?country=DE&status=paid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestUserFinanceRegression:
    """Regression tests for user finance screens"""

    def test_user_invoices_list(self, user_token):
        """GET /api/account/invoices returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/invoices",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_user_payments_list(self, user_token):
        """GET /api/account/payments returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/payments",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    def test_user_subscription_status(self, user_token):
        """GET /api/account/subscription returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Should have has_subscription field
        assert "has_subscription" in data

    def test_user_subscription_plans(self, user_token):
        """GET /api/account/subscription/plans returns 200"""
        response = requests.get(
            f"{BASE_URL}/api/account/subscription/plans",
            headers={"Authorization": f"Bearer {user_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestHealthEndpoint:
    """Health endpoint tests"""

    def test_health_check(self):
        """GET /api/health returns healthy"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "healthy"
        assert data.get("db_status") == "ok"

    def test_db_health(self):
        """GET /api/health/db returns ok"""
        response = requests.get(f"{BASE_URL}/api/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data.get("db_status") == "ok"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
