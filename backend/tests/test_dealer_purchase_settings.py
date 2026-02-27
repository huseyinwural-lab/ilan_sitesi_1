"""
Test cases for Dealer Purchase (Satın Al) and Account Settings (Hesabım) pages.
Covers:
- GET /api/dealer/invoices
- GET /api/pricing/packages
- GET /api/dealer/settings/profile
- PATCH /api/dealer/settings/profile
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
DEALER_EMAIL = "dealer1772201722@example.com"
DEALER_PASSWORD = "Dealer123!"


@pytest.fixture(scope="module")
def dealer_token():
    """Authenticate as dealer and return access token."""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": DEALER_EMAIL, "password": DEALER_PASSWORD},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, "No access token in response"
    return data["access_token"]


@pytest.fixture
def auth_headers(dealer_token):
    """Return authorization headers with dealer token."""
    return {
        "Authorization": f"Bearer {dealer_token}",
        "Content-Type": "application/json",
    }


class TestDealerInvoices:
    """Tests for GET /api/dealer/invoices endpoint"""

    def test_dealer_invoices_returns_200(self, auth_headers):
        """GET /api/dealer/invoices should return 200 with items array"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/invoices",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_dealer_invoices_requires_auth(self):
        """GET /api/dealer/invoices without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/dealer/invoices")
        assert response.status_code == 401

    def test_dealer_invoices_with_status_filter(self, auth_headers):
        """GET /api/dealer/invoices with status filter should return filtered results"""
        for status in ["issued", "paid", "overdue", "cancelled"]:
            response = requests.get(
                f"{BASE_URL}/api/dealer/invoices?status={status}",
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert "items" in data

    def test_dealer_invoices_invalid_status(self, auth_headers):
        """GET /api/dealer/invoices with invalid status should return 400"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/invoices?status=invalid_status",
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestPricingPackages:
    """Tests for GET /api/pricing/packages endpoint (public)"""

    def test_pricing_packages_returns_200(self):
        """GET /api/pricing/packages should return 200 with packages array"""
        response = requests.get(f"{BASE_URL}/api/pricing/packages")
        assert response.status_code == 200
        data = response.json()
        assert "packages" in data
        assert isinstance(data["packages"], list)

    def test_pricing_packages_structure(self):
        """GET /api/pricing/packages response structure validation"""
        response = requests.get(f"{BASE_URL}/api/pricing/packages")
        assert response.status_code == 200
        data = response.json()
        # Even if empty, packages key should exist
        assert "packages" in data
        # If packages exist, validate structure
        for pkg in data.get("packages", []):
            assert "id" in pkg
            assert "name" in pkg
            assert "listing_quota" in pkg
            assert "price_amount" in pkg


class TestDealerSettingsProfile:
    """Tests for GET/PATCH /api/dealer/settings/profile endpoints"""

    def test_dealer_settings_profile_get_200(self, auth_headers):
        """GET /api/dealer/settings/profile should return 200 with profile data"""
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "profile" in data
        profile = data["profile"]
        # Validate required fields exist
        assert "company_name" in profile
        assert "authorized_person" in profile
        assert "contact_email" in profile
        assert "contact_phone" in profile
        assert "address_street" in profile
        assert "address_zip" in profile
        assert "address_city" in profile
        assert "address_country" in profile
        assert "logo_url" in profile

    def test_dealer_settings_profile_requires_auth(self):
        """GET /api/dealer/settings/profile without auth should return 401"""
        response = requests.get(f"{BASE_URL}/api/dealer/settings/profile")
        assert response.status_code == 401

    def test_dealer_settings_profile_patch_success(self, auth_headers):
        """PATCH /api/dealer/settings/profile should update profile"""
        # Get current profile first
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        original_phone = response.json()["profile"]["contact_phone"]

        # Update phone
        new_phone = "+49999888777"
        update_response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
            json={"contact_phone": new_phone},
        )
        assert update_response.status_code == 200
        assert update_response.json().get("ok") is True

        # Verify update persisted
        verify_response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
        )
        assert verify_response.status_code == 200
        assert verify_response.json()["profile"]["contact_phone"] == new_phone

        # Revert to original
        requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
            json={"contact_phone": original_phone},
        )

    def test_dealer_settings_profile_patch_requires_auth(self):
        """PATCH /api/dealer/settings/profile without auth should return 401"""
        response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            json={"contact_phone": "+49111222333"},
        )
        assert response.status_code == 401

    def test_dealer_settings_profile_update_company_name(self, auth_headers):
        """PATCH /api/dealer/settings/profile - update company_name"""
        # Get current company_name
        response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
        )
        assert response.status_code == 200
        original_name = response.json()["profile"]["company_name"]

        # Update company name
        new_name = "TEST_Company_Update"
        update_response = requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
            json={"company_name": new_name},
        )
        assert update_response.status_code == 200

        # Verify
        verify_response = requests.get(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
        )
        assert verify_response.json()["profile"]["company_name"] == new_name

        # Revert
        requests.patch(
            f"{BASE_URL}/api/dealer/settings/profile",
            headers=auth_headers,
            json={"company_name": original_name},
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
