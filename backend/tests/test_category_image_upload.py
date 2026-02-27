"""
Tests for Category Image Upload Feature (Iteration 40)
- POST /api/admin/categories/image-upload endpoint
- Root-only image_url validation in create/update endpoints
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

@pytest.fixture(scope="module")
def auth_header():
    """Login as admin and return auth header"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@platform.com",
        "password": "Admin123!"
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    token = response.json().get("access_token")
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def root_category_id(auth_header):
    """Create a root category for testing"""
    import time
    slug = f"test-root-img-{int(time.time())}"
    response = requests.post(f"{BASE_URL}/api/admin/categories", 
        headers=auth_header,
        json={
            "name": "Test Root Category",
            "slug": slug,
            "module": "other",
            "country_code": "DE",
            "sort_order": 999,
            "active_flag": True
        }
    )
    assert response.status_code == 201, f"Root category creation failed: {response.text}"
    return response.json()["category"]["id"]

@pytest.fixture(scope="module")
def child_category_id(auth_header, root_category_id):
    """Create a child category for testing"""
    import time
    slug = f"test-child-img-{int(time.time())}"
    response = requests.post(f"{BASE_URL}/api/admin/categories", 
        headers=auth_header,
        json={
            "name": "Test Child Category",
            "slug": slug,
            "parent_id": root_category_id,
            "module": "other",
            "country_code": "DE",
            "sort_order": 1,
            "active_flag": True
        }
    )
    assert response.status_code == 201, f"Child category creation failed: {response.text}"
    return response.json()["category"]["id"]


class TestCategoryImageUpload:
    """Tests for POST /api/admin/categories/image-upload"""
    
    def test_upload_valid_png(self, auth_header):
        """Test uploading a valid PNG image"""
        # Create a simple 10x10 red PNG image
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            headers=auth_header,
            files={"file": ("test.png", buffer, "image/png")}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert "image_url" in data
        assert data["image_url"].startswith("/api/site/assets/")
        print(f"✓ Valid PNG upload successful: {data['image_url']}")
    
    def test_upload_valid_jpg(self, auth_header):
        """Test uploading a valid JPG image"""
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='blue')
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            headers=auth_header,
            files={"file": ("test.jpg", buffer, "image/jpeg")}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert "image_url" in data
        print(f"✓ Valid JPG upload successful: {data['image_url']}")
    
    def test_upload_valid_webp(self, auth_header):
        """Test uploading a valid WEBP image"""
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='green')
        buffer = io.BytesIO()
        img.save(buffer, format='WEBP')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            headers=auth_header,
            files={"file": ("test.webp", buffer, "image/webp")}
        )
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert data.get("ok") is True
        assert "image_url" in data
        print(f"✓ Valid WEBP upload successful: {data['image_url']}")
    
    def test_upload_invalid_format(self, auth_header):
        """Test uploading unsupported file format (txt)"""
        buffer = io.BytesIO(b"This is not an image")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            headers=auth_header,
            files={"file": ("test.txt", buffer, "text/plain")}
        )
        # Should fail with 400
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Invalid format correctly rejected")
    
    def test_upload_too_large(self, auth_header):
        """Test uploading image exceeding 2MB limit"""
        # Create a ~3MB image (should exceed 2MB limit)
        from PIL import Image
        img = Image.new('RGB', (2000, 2000), color='white')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # Check if the buffer is larger than 2MB
        size = buffer.getbuffer().nbytes
        if size <= 2 * 1024 * 1024:
            # If not large enough, create larger data
            buffer = io.BytesIO(b'x' * (3 * 1024 * 1024))
            buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            headers=auth_header,
            files={"file": ("large.png", buffer, "image/png")}
        )
        # Should fail with 400 for too large
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print("✓ Too large image correctly rejected")
    
    def test_upload_requires_auth(self):
        """Test that upload endpoint requires authentication"""
        from PIL import Image
        img = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/categories/image-upload",
            files={"file": ("test.png", buffer, "image/png")}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthenticated upload correctly rejected")


class TestCategoryCreateWithImage:
    """Tests for image_url in POST /api/admin/categories"""
    
    def test_root_category_with_image_url(self, auth_header):
        """Test creating root category with image_url (should succeed)"""
        import time
        slug = f"test-root-with-img-{int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/admin/categories", 
            headers=auth_header,
            json={
                "name": "Root With Image",
                "slug": slug,
                "module": "other",
                "country_code": "DE",
                "sort_order": 998,
                "active_flag": True,
                "image_url": "/api/site/assets/test-category.webp"
            }
        )
        assert response.status_code == 201, f"Root category with image failed: {response.text}"
        data = response.json()
        assert data["category"]["image_url"] == "/api/site/assets/test-category.webp"
        print("✓ Root category with image_url created successfully")
        return data["category"]["id"]
    
    def test_child_category_with_image_url_rejected(self, auth_header, root_category_id):
        """Test creating child category with image_url (should fail with CATEGORY_IMAGE_ROOT_ONLY)"""
        import time
        slug = f"test-child-with-img-{int(time.time())}"
        
        response = requests.post(f"{BASE_URL}/api/admin/categories", 
            headers=auth_header,
            json={
                "name": "Child With Image",
                "slug": slug,
                "parent_id": root_category_id,
                "module": "other",
                "country_code": "DE",
                "sort_order": 2,
                "active_flag": True,
                "image_url": "/api/site/assets/test-category.webp"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        # Check for CATEGORY_IMAGE_ROOT_ONLY error
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            error_code = detail.get("error_code", "")
        else:
            error_code = ""
        assert error_code == "CATEGORY_IMAGE_ROOT_ONLY" or "ana kategori" in str(detail).lower(), \
            f"Expected CATEGORY_IMAGE_ROOT_ONLY error, got: {data}"
        print("✓ Child category with image_url correctly rejected (CATEGORY_IMAGE_ROOT_ONLY)")


class TestCategoryUpdateWithImage:
    """Tests for image_url in PATCH /api/admin/categories/{id}"""
    
    def test_update_root_with_image_url(self, auth_header, root_category_id):
        """Test updating root category with image_url (should succeed)"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{root_category_id}",
            headers=auth_header,
            json={
                "image_url": "/api/site/assets/updated-category.webp"
            }
        )
        assert response.status_code == 200, f"Update root with image failed: {response.text}"
        data = response.json()
        assert data["category"]["image_url"] == "/api/site/assets/updated-category.webp"
        print("✓ Root category image_url updated successfully")
    
    def test_update_child_with_image_url_rejected(self, auth_header, child_category_id):
        """Test updating child category with image_url (should fail with CATEGORY_IMAGE_ROOT_ONLY)"""
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{child_category_id}",
            headers=auth_header,
            json={
                "image_url": "/api/site/assets/test-category.webp"
            }
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        data = response.json()
        detail = data.get("detail", {})
        if isinstance(detail, dict):
            error_code = detail.get("error_code", "")
        else:
            error_code = ""
        assert error_code == "CATEGORY_IMAGE_ROOT_ONLY" or "ana kategori" in str(detail).lower(), \
            f"Expected CATEGORY_IMAGE_ROOT_ONLY error, got: {data}"
        print("✓ Child category image_url update correctly rejected (CATEGORY_IMAGE_ROOT_ONLY)")
    
    def test_remove_root_image(self, auth_header, root_category_id):
        """Test removing image from root category"""
        # First add an image
        requests.patch(
            f"{BASE_URL}/api/admin/categories/{root_category_id}",
            headers=auth_header,
            json={"image_url": "/api/site/assets/temp.webp"}
        )
        
        # Now remove it
        response = requests.patch(
            f"{BASE_URL}/api/admin/categories/{root_category_id}",
            headers=auth_header,
            json={"image_url": ""}
        )
        assert response.status_code == 200, f"Remove root image failed: {response.text}"
        data = response.json()
        # image_url should be empty or None
        assert not data["category"].get("image_url"), f"image_url should be empty, got: {data['category'].get('image_url')}"
        print("✓ Root category image_url removed successfully")


class TestCategoryImagePreview:
    """Tests for image preview URL with cache busting"""
    
    def test_image_url_persisted_in_get(self, auth_header, root_category_id):
        """Test that image_url is returned in GET category response"""
        # First set an image
        requests.patch(
            f"{BASE_URL}/api/admin/categories/{root_category_id}",
            headers=auth_header,
            json={"image_url": "/api/site/assets/persist-test.webp"}
        )
        
        # Then GET and verify
        response = requests.get(
            f"{BASE_URL}/api/admin/categories/{root_category_id}",
            headers=auth_header
        )
        assert response.status_code == 200, f"GET category failed: {response.text}"
        data = response.json()
        assert data["category"]["image_url"] == "/api/site/assets/persist-test.webp"
        print("✓ image_url correctly persisted and returned in GET")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
