"""
P60 Sprint 2 Tests: Corporate Header 3-Row Drag&Drop + Logo Upload
- Corporate header guardrails: 3-row enforcement, row1 logo requirement
- Logo upload validation: format (png/svg/webp), max 2MB, aspect ratio 3:1 (±10%)
- Logo upload persistence and effective resolve
- Cleanup endpoint for replaced logos
"""
import pytest
import requests
import os
import uuid
import io
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"
DEALER_EMAIL = "dealer@platform.com"
DEALER_PASSWORD = "Dealer123!"


def get_auth_token(email: str, password: str, portal: str = "admin") -> str:
    """Login and get access token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": email, "password": password},
        headers={"X-Portal-Scope": portal}
    )
    if response.status_code != 200:
        pytest.skip(f"Login failed for {email}: {response.status_code} - {response.text[:200]}")
    data = response.json()
    return data.get("access_token") or data.get("token")


def create_test_image(width: int, height: int, fmt: str = "PNG") -> bytes:
    """Create a test image with given dimensions and format"""
    img = Image.new('RGB', (width, height), color=(255, 255, 0))
    buffer = io.BytesIO()
    img.save(buffer, format=fmt)
    buffer.seek(0)
    return buffer.read()


def create_test_svg(width: int, height: int) -> bytes:
    """Create a test SVG with given dimensions"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="{width}" height="{height}" fill="#FFDD00"/>
  <text x="{width//2}" y="{height//2}" text-anchor="middle" fill="#000">TEST</text>
</svg>'''.encode('utf-8')


def get_error_detail(response):
    payload = response.json()
    detail = payload.get("detail")
    if isinstance(detail, dict):
        return detail
    return {"code": None, "message": str(detail or "")}


@pytest.fixture(scope="module")
def admin_token():
    """Get admin token for tests"""
    return get_auth_token(ADMIN_EMAIL, ADMIN_PASSWORD, "admin")


@pytest.fixture(scope="module")
def dealer_token():
    """Get dealer token for tests"""
    return get_auth_token(DEALER_EMAIL, DEALER_PASSWORD, "dealer")


class TestCorporateHeaderGuardrails:
    """Test corporate header 3-row enforcement and row1 logo requirement"""
    
    def test_corporate_header_normalizes_to_3_rows(self, admin_token):
        """Corporate header normalizes partial config to always have 3 rows"""
        # Config with only 2 rows - normalization fills in missing row from defaults
        partial_config = {
            "rows": [
                {"id": "row1", "title": "Row 1", "blocks": [{"id": "logo", "type": "logo", "label": "Logo"}]},
                {"id": "row2", "title": "Row 2", "blocks": [{"id": "test", "type": "test", "label": "Test"}]},
            ],
            "logo": {"url": None, "fallback_text": "ANNONCIA"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "system",
                "status": "draft",
                "config_data": partial_config
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        # Normalization fills in row3 from defaults, so 200 is expected
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        result = response.json()
        config_data = result.get("item", {}).get("config_data", {})
        rows = config_data.get("rows", [])
        assert len(rows) == 3, f"Expected 3 rows after normalization, got {len(rows)}"
        row_ids = [row.get("id") for row in rows]
        assert row_ids == ["row1", "row2", "row3"]
        print("✓ Corporate header normalizes to 3 rows from partial input")
    
    def test_corporate_header_row1_requires_logo(self, admin_token):
        """Corporate header POST should reject row1 without logo block"""
        # Config without logo in row1
        invalid_config = {
            "rows": [
                {"id": "row1", "title": "Row 1", "blocks": [{"id": "nav", "type": "nav", "label": "Nav"}]},
                {"id": "row2", "title": "Row 2", "blocks": [{"id": "test", "type": "test", "label": "Test"}]},
                {"id": "row3", "title": "Row 3", "blocks": [{"id": "user", "type": "user_menu", "label": "User"}]},
            ],
            "logo": {"url": None, "fallback_text": "ANNONCIA"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "system",
                "status": "draft",
                "config_data": invalid_config
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:200]}"
        error_detail = get_error_detail(response)
        assert "logo" in (error_detail.get("message") or "").lower()
        print("✓ Corporate header correctly rejects row1 without logo block")
    
    def test_corporate_header_valid_config_accepted(self, admin_token):
        """Corporate header POST should accept valid 3-row config with logo"""
        valid_config = {
            "rows": [
                {"id": "row1", "title": "Row 1", "blocks": [
                    {"id": "logo", "type": "logo", "label": "Logo", "required": True},
                    {"id": "quick_actions", "type": "quick_actions", "label": "Quick Actions"}
                ]},
                {"id": "row2", "title": "Row 2", "blocks": [
                    {"id": "modules", "type": "modules", "label": "Modules"}
                ]},
                {"id": "row3", "title": "Row 3", "blocks": [
                    {"id": "user_menu", "type": "user_menu", "label": "User Menu"}
                ]},
            ],
            "logo": {"url": None, "fallback_text": "ANNONCIA"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "system",
                "status": "draft",
                "config_data": valid_config
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert data.get("ok") is True
        assert data["item"]["segment"] == "corporate"
        print(f"✓ Valid corporate header config accepted: version={data['item']['version']}")
    
    def test_corporate_header_rows_must_have_blocks(self, admin_token):
        """Corporate header POST should reject rows with empty blocks"""
        invalid_config = {
            "rows": [
                {"id": "row1", "title": "Row 1", "blocks": [{"id": "logo", "type": "logo", "label": "Logo"}]},
                {"id": "row2", "title": "Row 2", "blocks": []},  # Empty blocks
                {"id": "row3", "title": "Row 3", "blocks": [{"id": "user", "type": "user_menu", "label": "User"}]},
            ],
            "logo": {"url": None, "fallback_text": "ANNONCIA"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header",
            json={
                "segment": "corporate",
                "scope": "system",
                "status": "draft",
                "config_data": invalid_config
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text[:200]}"
        print("✓ Corporate header correctly rejects rows with empty blocks")


class TestLogoUploadValidation:
    """Test logo upload endpoint validation"""
    
    def test_logo_upload_valid_3_1_png(self, admin_token):
        """Upload valid 3:1 aspect ratio PNG should succeed"""
        # 300x100 = 3:1 ratio
        img_data = create_test_image(300, 100, "PNG")
        
        files = {"file": ("test_logo.png", img_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        result = response.json()
        assert result.get("ok") is True
        assert result.get("logo_url") is not None
        assert result.get("logo_meta", {}).get("width") == 300
        assert result.get("logo_meta", {}).get("height") == 100
        print(f"✓ Valid 3:1 PNG upload accepted: url={result['logo_url']}")
    
    def test_logo_upload_valid_svg(self, admin_token):
        """Upload valid 3:1 aspect ratio SVG should succeed"""
        # 600x200 = 3:1 ratio
        svg_data = create_test_svg(600, 200)
        
        files = {"file": ("test_logo.svg", svg_data, "image/svg+xml")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        result = response.json()
        assert result.get("ok") is True
        print(f"✓ Valid 3:1 SVG upload accepted: url={result['logo_url']}")
    
    def test_logo_upload_invalid_ratio_rejected(self, admin_token):
        """Upload with invalid aspect ratio (not ~3:1) should be rejected"""
        # 200x200 = 1:1 ratio (invalid)
        img_data = create_test_image(200, 200, "PNG")
        
        files = {"file": ("bad_ratio.png", img_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid ratio, got {response.status_code}"
        error_detail = get_error_detail(response)
        assert error_detail.get("code") in {"INVALID_ASPECT_RATIO", None}
        assert "ratio" in (error_detail.get("message") or "").lower() or "oran" in (error_detail.get("message") or "").lower()
        print("✓ Invalid aspect ratio correctly rejected")
    
    def test_logo_upload_valid_ratio_with_tolerance(self, admin_token):
        """Upload with ratio within ±10% tolerance should succeed"""
        # 310x100 = 3.1:1 ratio (within 10% tolerance of 3:1)
        img_data = create_test_image(310, 100, "PNG")
        
        files = {"file": ("tolerance_logo.png", img_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✓ Valid ratio with tolerance accepted")
    
    def test_logo_upload_invalid_format_rejected(self, admin_token):
        """Upload with unsupported format (e.g., gif) should be rejected"""
        img_data = create_test_image(300, 100, "GIF")
        
        files = {"file": ("bad_format.gif", img_data, "image/gif")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400 for invalid format, got {response.status_code}"
        error_detail = get_error_detail(response)
        assert error_detail.get("code") in {"INVALID_FILE_TYPE", None}
        print("✓ Invalid format correctly rejected")
    
    def test_logo_upload_exceeds_max_size_rejected(self, admin_token):
        """Upload exceeding 2MB should be rejected"""
        # Create a large image (> 2MB)
        large_img = Image.new('RGB', (5000, 5000), color=(255, 255, 0))
        buffer = io.BytesIO()
        large_img.save(buffer, format='PNG')
        buffer.seek(0)
        large_data = buffer.read()
        
        # Ensure it's > 2MB
        if len(large_data) <= 2 * 1024 * 1024:
            pytest.skip("Generated image not large enough for size test")
        
        files = {"file": ("large_logo.png", large_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400 for oversized file, got {response.status_code}"
        error_detail = get_error_detail(response)
        assert error_detail.get("code") in {"FILE_TOO_LARGE", None}
        print("✓ Oversized file correctly rejected")
    
    def test_logo_upload_webp_format(self, admin_token):
        """Upload valid webp format should succeed"""
        img_data = create_test_image(300, 100, "WEBP")
        
        files = {"file": ("test_logo.webp", img_data, "image/webp")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✓ Valid WEBP upload accepted")
    
    def test_logo_upload_non_corporate_rejected(self, admin_token):
        """Upload to non-corporate segment should be rejected (Sprint 2 scope)"""
        img_data = create_test_image(300, 100, "PNG")
        
        files = {"file": ("test_logo.png", img_data, "image/png")}
        data = {"segment": "individual", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400 for non-corporate segment, got {response.status_code}"
        print("✓ Non-corporate segment correctly rejected")


class TestLogoPersistenceAndEffective:
    """Test logo upload persistence in draft and publish->effective flow"""
    
    def test_logo_upload_creates_draft_with_logo_url(self, admin_token):
        """After logo upload, draft config should have logo.url populated"""
        img_data = create_test_image(300, 100, "PNG")
        
        files = {"file": ("persist_test.png", img_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        result = response.json()
        
        config_data = result.get("item", {}).get("config_data", {})
        logo_url = config_data.get("logo", {}).get("url")
        assert logo_url is not None and logo_url.startswith("/api/site/assets/")
        print(f"✓ Draft created with logo.url: {logo_url}")
        return result["item"]["id"], logo_url
    
    def test_published_corporate_header_has_logo_in_effective(self, admin_token, dealer_token):
        """After upload and publish, effective endpoint should return logo.url"""
        # Step 1: Upload logo
        img_data = create_test_image(300, 100, "PNG")
        files = {"file": ("effective_test.png", img_data, "image/png")}
        data = {"segment": "corporate", "scope": "system"}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/logo",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert upload_response.status_code == 200
        config_id = upload_response.json()["item"]["id"]
        config_version = upload_response.json()["item"].get("version")
        uploaded_logo_url = upload_response.json()["logo_url"]
        
        # Step 2: Publish
        publish_response = requests.post(
            f"{BASE_URL}/api/admin/ui/configs/header/publish/{config_id}",
            json={
                "config_version": config_version,
                "owner_type": "global",
                "owner_id": "global",
            },
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert publish_response.status_code == 200
        
        # Step 3: Check effective
        effective_response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=corporate",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert effective_response.status_code == 200
        effective_data = effective_response.json()
        
        effective_logo_url = effective_data.get("config_data", {}).get("logo", {}).get("url")
        assert effective_logo_url == uploaded_logo_url, f"Expected {uploaded_logo_url}, got {effective_logo_url}"
        print(f"✓ Effective config has logo.url: {effective_logo_url}")


class TestLogoCleanup:
    """Test logo asset cleanup endpoint"""
    
    def test_cleanup_endpoint_returns_200(self, admin_token):
        """POST /api/admin/ui/logo-assets/cleanup should return 200"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/logo-assets/cleanup",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        data = response.json()
        assert data.get("ok") is True
        assert "deleted" in data
        assert "skipped" in data
        assert "pending" in data
        assert "retention_days" in data
        print(f"✓ Cleanup endpoint returned: deleted={data['deleted']}, skipped={data['skipped']}, pending={data['pending']}")
    
    def test_cleanup_endpoint_dealer_403(self, dealer_token):
        """Dealer should get 403 on cleanup endpoint"""
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/logo-assets/cleanup",
            headers={"Authorization": f"Bearer {dealer_token}"}
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"
        print("✓ Dealer correctly denied cleanup endpoint")


class TestThemeTokenValidation:
    """Test theme token form validation (Sprint 2 addition)"""
    
    def test_theme_colors_hex_validation(self, admin_token):
        """Theme colors must be valid hex format"""
        invalid_tokens = {
            "colors": {
                "primary": "not-a-hex",  # Invalid
                "secondary": "#334155"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": f"Invalid Color Theme {uuid.uuid4().hex[:8]}", "tokens": invalid_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "hex" in response.json().get("detail", "").lower()
        print("✓ Invalid hex color correctly rejected")
    
    def test_theme_spacing_range_validation(self, admin_token):
        """Theme spacing must be 0-64"""
        invalid_tokens = {
            "spacing": {"xs": 100}  # > 64, invalid
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": f"Invalid Spacing Theme {uuid.uuid4().hex[:8]}", "tokens": invalid_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid spacing range correctly rejected")
    
    def test_theme_radius_range_validation(self, admin_token):
        """Theme radius must be 0-32"""
        invalid_tokens = {
            "radius": {"sm": 50}  # > 32, invalid
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": f"Invalid Radius Theme {uuid.uuid4().hex[:8]}", "tokens": invalid_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid radius range correctly rejected")
    
    def test_theme_base_font_size_range_validation(self, admin_token):
        """Theme base_font_size must be 12-24"""
        invalid_tokens = {
            "typography": {"base_font_size": 30}  # > 24, invalid
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": f"Invalid FontSize Theme {uuid.uuid4().hex[:8]}", "tokens": invalid_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ Invalid base_font_size range correctly rejected")
    
    def test_theme_valid_tokens_accepted(self, admin_token):
        """Valid token values should be accepted"""
        valid_tokens = {
            "colors": {
                "primary": "#111827",
                "secondary": "#334155",
                "accent": "#f97316",
                "text": "#0f172a",
                "inverse": "#ffffff"
            },
            "typography": {
                "font_family": "Poppins",
                "base_font_size": 16
            },
            "spacing": {
                "xs": 4,
                "sm": 8,
                "md": 12,
                "lg": 16,
                "xl": 24
            },
            "radius": {
                "sm": 4,
                "md": 8,
                "lg": 12
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/ui/themes",
            json={"name": f"Valid Token Theme {uuid.uuid4().hex[:8]}", "tokens": valid_tokens},
            headers={"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text[:200]}"
        print("✓ Valid tokens accepted")


class TestConfigDrivenRender:
    """Test config-driven render: logo resolve, fallback behavior"""
    
    def test_corporate_header_fallback_when_no_logo(self, admin_token):
        """When no logo.url, config_data should have fallback_text"""
        response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=corporate",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        config_data = response.json().get("config_data", {})
        logo = config_data.get("logo", {})
        fallback_text = logo.get("fallback_text")
        assert fallback_text is not None and fallback_text != ""
        print(f"✓ Fallback text present: {fallback_text}")
    
    def test_individual_header_fallback(self, admin_token):
        """Individual header should also have fallback when no config"""
        response = requests.get(
            f"{BASE_URL}/api/ui/header?segment=individual",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        config_data = response.json().get("config_data", {})
        logo = config_data.get("logo", {})
        # Should have fallback_text or at least the logo structure
        assert "fallback_text" in logo or logo.get("url") is None
        print("✓ Individual header fallback working")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
