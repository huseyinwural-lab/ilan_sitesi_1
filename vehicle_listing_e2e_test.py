#!/usr/bin/env python3
"""
Vehicle Listing E2E Backend Tests - Stage 4
Re-run tests to ensure still passing after latest changes.

Focus on:
- create draft
- upload 3 images  
- submit publish
- detail
- public media
- negative: invalid make, 2 photos, draft media not public
"""

import requests
import json
import io
from PIL import Image
import sys
from datetime import datetime

class VehicleListingE2ETester:
    def __init__(self, base_url="https://admin-final-sprint.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []
        self.listing_id = None

    def log(self, message):
        """Log test output"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, files=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        test_headers = {}
        
        if headers:
            test_headers.update(headers)
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'

        # Don't set Content-Type for multipart uploads
        if not files and method in ['POST', 'PATCH']:
            test_headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        self.log(f"   URL: {url}")
        self.log(f"   Method: {method}")
        self.log(f"   Expected Status: {expected_status}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, headers=test_headers)
                else:
                    response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers)

            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Status: {response.status_code}")
                try:
                    resp_data = response.json()
                    self.log(f"   Response: {json.dumps(resp_data, indent=2)[:200]}...")
                    return True, resp_data
                except:
                    return True, response.text
            else:
                self.log(f"❌ FAILED - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {json.dumps(error_data, indent=2)}")
                except:
                    self.log(f"   Error: {response.text}")
                
                self.failures.append({
                    'test': name,
                    'expected': expected_status,
                    'actual': response.status_code,
                    'endpoint': endpoint,
                    'response': response.text[:500]
                })
                return False, {}

        except Exception as e:
            self.log(f"❌ FAILED - Exception: {str(e)}")
            self.failures.append({
                'test': name,
                'error': str(e),
                'endpoint': endpoint
            })
            return False, {}

    def login_admin(self):
        """Login with admin credentials"""
        self.log("🔐 Logging in as admin...")
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "/auth/login",
            200,
            data={"email": "admin@platform.com", "password": "Admin123!"}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            self.log(f"   ✅ Logged in as: {self.user['full_name']} ({self.user['role']})")
            return True
        return False

    def create_test_image(self, width=800, height=600, color=(255, 0, 0)):
        """Create a test image in memory"""
        img = Image.new('RGB', (width, height), color)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=85)
        img_bytes.seek(0)
        return img_bytes

    def test_create_valid_draft(self):
        """Test creating a valid vehicle draft"""
        self.log("📝 Creating valid vehicle draft...")
        
        draft_data = {
            "country": "DE",
            "category_key": "otomobil",
            "make_key": "bmw",
            "model_key": "3-serie",
            "year": 2020,
            "fuel_type": "benzin",
            "transmission": "manuel",
            "mileage_km": 50000,
            "price_eur": 25000,
            "condition": "ikinci-el",
            "power_hp": 184
        }
        
        success, response = self.run_test(
            "Create Valid Draft",
            "POST",
            "/v1/listings/vehicle",
            200,
            data=draft_data
        )
        
        if success and 'id' in response:
            self.listing_id = response['id']
            self.log(f"   ✅ Draft created with ID: {self.listing_id}")
            self.log(f"   Status: {response.get('status')}")
            self.log(f"   Next Actions: {response.get('next_actions')}")
            return True
        return False

    def test_upload_3_images(self):
        """Test uploading 3 images to the draft"""
        if not self.listing_id:
            self.log("❌ No listing ID available for image upload")
            return False
            
        self.log("📸 Uploading 3 test images...")
        
        # Create 3 test images with different colors
        files = []
        colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        
        for i, color in enumerate(colors):
            img_bytes = self.create_test_image(800, 600, color)
            files.append(('files', (f'test_image_{i+1}.jpg', img_bytes, 'image/jpeg')))
        
        success, response = self.run_test(
            "Upload 3 Images",
            "POST",
            f"/v1/listings/vehicle/{self.listing_id}/media",
            200,
            files=files
        )
        
        if success:
            media = response.get('media', [])
            self.log(f"   ✅ Uploaded {len(media)} images")
            for i, m in enumerate(media):
                self.log(f"   Image {i+1}: {m['width']}x{m['height']}, Cover: {m.get('is_cover', False)}")
            return True
        return False

    def test_submit_for_publication(self):
        """Test submitting the draft for publication"""
        if not self.listing_id:
            self.log("❌ No listing ID available for submission")
            return False
            
        self.log("🚀 Submitting draft for publication...")
        
        success, response = self.run_test(
            "Submit for Publication",
            "POST",
            f"/v1/listings/vehicle/{self.listing_id}/submit",
            200
        )
        
        if success:
            self.log(f"   ✅ Status: {response.get('status')}")
            self.log(f"   Detail URL: {response.get('detail_url')}")
            self.log(f"   Next Actions: {response.get('next_actions')}")
            return True
        return False

    def test_get_published_detail(self):
        """Test getting the published listing detail"""
        if not self.listing_id:
            self.log("❌ No listing ID available for detail retrieval")
            return False
            
        self.log("📋 Getting published listing detail...")
        
        success, response = self.run_test(
            "Get Published Detail",
            "GET",
            f"/v1/listings/vehicle/{self.listing_id}",
            200
        )
        
        if success:
            self.log(f"   ✅ Status: {response.get('status')}")
            self.log(f"   Country: {response.get('country')}")
            self.log(f"   Category: {response.get('category_key')}")
            vehicle = response.get('vehicle', {})
            self.log(f"   Vehicle: {vehicle.get('make_key')} {vehicle.get('model_key')} {vehicle.get('year')}")
            media = response.get('media', [])
            self.log(f"   Media Count: {len(media)}")
            for i, m in enumerate(media):
                self.log(f"   Media {i+1}: {m.get('url')}, Cover: {m.get('is_cover', False)}")
            return True, response
        return False, {}

    def test_public_media_access(self, detail_response):
        """Test accessing public media files"""
        if not detail_response:
            self.log("❌ No detail response available for media testing")
            return False
            
        media = detail_response.get('media', [])
        if not media:
            self.log("❌ No media found in detail response")
            return False
            
        self.log("🖼️ Testing public media access...")
        
        # Test first media file
        first_media = media[0]
        media_url = first_media.get('url', '')
        
        if not media_url.startswith('/media/'):
            self.log(f"❌ Invalid media URL format: {media_url}")
            return False
            
        # Remove /media/ prefix and construct full URL
        media_path = media_url[7:]  # Remove '/media/' prefix
        full_url = f"{self.base_url}/media/{media_path}"
        
        self.log(f"   Testing URL: {full_url}")
        
        try:
            response = requests.get(full_url)
            success = response.status_code == 200
            
            if success:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Public Media Access - Status: {response.status_code}")
                self.log(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
                self.log(f"   Content-Length: {len(response.content)} bytes")
                return True
            else:
                self.log(f"❌ FAILED - Public Media Access - Status: {response.status_code}")
                self.failures.append({
                    'test': 'Public Media Access',
                    'expected': 200,
                    'actual': response.status_code,
                    'endpoint': media_url
                })
                return False
                
        except Exception as e:
            self.log(f"❌ FAILED - Public Media Access - Exception: {str(e)}")
            self.failures.append({
                'test': 'Public Media Access',
                'error': str(e),
                'endpoint': media_url
            })
            return False
        finally:
            self.tests_run += 1

    def test_invalid_make_validation(self):
        """Test validation with invalid make"""
        self.log("🚫 Testing invalid make validation...")
        
        invalid_draft_data = {
            "country": "DE",
            "category_key": "otomobil",
            "make_key": "not-a-make",  # Invalid make
            "model_key": "3-serie",
            "year": 2020,
            "fuel_type": "benzin",
            "transmission": "manuel",
            "mileage_km": 50000,
            "price_eur": 25000,
            "condition": "ikinci-el",
            "power_hp": 184
        }
        
        # Create draft first
        success, response = self.run_test(
            "Create Draft with Invalid Make",
            "POST",
            "/v1/listings/vehicle",
            200,
            data=invalid_draft_data
        )
        
        if not success:
            return False
            
        invalid_listing_id = response.get('id')
        if not invalid_listing_id:
            self.log("❌ No listing ID returned for invalid make test")
            return False
        
        # Upload minimum required images (3)
        files = []
        for i in range(3):
            img_bytes = self.create_test_image(800, 600, (128, 128, 128))
            files.append(('files', (f'invalid_test_{i+1}.jpg', img_bytes, 'image/jpeg')))
        
        upload_success, _ = self.run_test(
            "Upload Images for Invalid Make Test",
            "POST",
            f"/v1/listings/vehicle/{invalid_listing_id}/media",
            200,
            files=files
        )
        
        if not upload_success:
            return False
        
        # Now try to submit - should fail with validation error
        success, response = self.run_test(
            "Submit Invalid Make (Should Fail)",
            "POST",
            f"/v1/listings/vehicle/{invalid_listing_id}/submit",
            422  # Expecting validation error
        )
        
        if success:
            validation_errors = response.get('detail', {}).get('validation_errors', [])
            self.log(f"   ✅ Validation errors found: {len(validation_errors)}")
            for error in validation_errors:
                self.log(f"   Error: {error.get('field')} - {error.get('code')} - {error.get('message')}")
            
            # Check for MAKE_NOT_FOUND error
            make_error = next((e for e in validation_errors if e.get('code') == 'MAKE_NOT_FOUND'), None)
            if make_error:
                self.log(f"   ✅ MAKE_NOT_FOUND error correctly detected")
                return True
            else:
                self.log(f"   ❌ MAKE_NOT_FOUND error not found in validation errors")
                return False
        return False

    def test_insufficient_photos_validation(self):
        """Test validation with only 2 photos (minimum is 3)"""
        self.log("🚫 Testing insufficient photos validation...")
        
        draft_data = {
            "country": "DE",
            "category_key": "otomobil",
            "make_key": "bmw",
            "model_key": "3-serie",
            "year": 2020,
            "fuel_type": "benzin",
            "transmission": "manuel",
            "mileage_km": 50000,
            "price_eur": 25000,
            "condition": "ikinci-el",
            "power_hp": 184
        }
        
        # Create draft first
        success, response = self.run_test(
            "Create Draft for Photo Test",
            "POST",
            "/v1/listings/vehicle",
            200,
            data=draft_data
        )
        
        if not success:
            return False
            
        photo_test_listing_id = response.get('id')
        if not photo_test_listing_id:
            self.log("❌ No listing ID returned for photo test")
            return False
        
        # Upload only 2 images (insufficient)
        files = []
        for i in range(2):
            img_bytes = self.create_test_image(800, 600, (64, 64, 64))
            files.append(('files', (f'insufficient_test_{i+1}.jpg', img_bytes, 'image/jpeg')))
        
        upload_success, _ = self.run_test(
            "Upload Only 2 Images",
            "POST",
            f"/v1/listings/vehicle/{photo_test_listing_id}/media",
            200,
            files=files
        )
        
        if not upload_success:
            return False
        
        # Now try to submit - should fail with validation error
        success, response = self.run_test(
            "Submit with Insufficient Photos (Should Fail)",
            "POST",
            f"/v1/listings/vehicle/{photo_test_listing_id}/submit",
            422  # Expecting validation error
        )
        
        if success:
            validation_errors = response.get('detail', {}).get('validation_errors', [])
            self.log(f"   ✅ Validation errors found: {len(validation_errors)}")
            for error in validation_errors:
                self.log(f"   Error: {error.get('field')} - {error.get('code')} - {error.get('message')}")
            
            # Check for MIN_PHOTOS error
            photo_error = next((e for e in validation_errors if e.get('code') == 'MIN_PHOTOS'), None)
            if photo_error:
                self.log(f"   ✅ MIN_PHOTOS error correctly detected")
                return True
            else:
                self.log(f"   ❌ MIN_PHOTOS error not found in validation errors")
                return False
        return False

    def run_all_tests(self):
        """Run all Stage-4 backend E2E tests"""
        self.log("🚀 Starting Vehicle Listing E2E Backend Tests - Stage 4")
        self.log("=" * 60)
        
        # Login first
        if not self.login_admin():
            self.log("❌ Login failed, stopping tests")
            return False
        
        # Positive flow tests
        self.log("\n📋 POSITIVE FLOW TESTS")
        self.log("-" * 30)
        
        success_steps = []
        
        # Step 1: Create draft
        if self.test_create_valid_draft():
            success_steps.append("create_draft")
        
        # Step 2: Upload 3 images
        if self.test_upload_3_images():
            success_steps.append("upload_images")
        
        # Step 3: Submit for publication
        if self.test_submit_for_publication():
            success_steps.append("submit_publish")
        
        # Step 4: Get detail
        detail_success, detail_response = self.test_get_published_detail()
        if detail_success:
            success_steps.append("get_detail")
        
        # Step 5: Public media access
        if self.test_public_media_access(detail_response):
            success_steps.append("public_media")
        
        # Negative validation tests
        self.log("\n🚫 NEGATIVE VALIDATION TESTS")
        self.log("-" * 30)
        
        # Test invalid make
        if self.test_invalid_make_validation():
            success_steps.append("invalid_make")
        
        # Test insufficient photos
        if self.test_insufficient_photos_validation():
            success_steps.append("insufficient_photos")
        
        # Test draft media not public
        if self.test_draft_media_not_public():
            success_steps.append("draft_media_protected")
        
        # Print results
        self.log("\n" + "=" * 60)
        self.log("📊 TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        self.log(f"Tests Run: {self.tests_run}")
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        self.log(f"\n✅ Successful Steps: {', '.join(success_steps)}")
        
        if self.failures:
            self.log(f"\n❌ Failed Tests ({len(self.failures)}):")
            for failure in self.failures:
                error_msg = failure.get('error', f"Status {failure.get('actual')} != {failure.get('expected')}")
                self.log(f"  • {failure['test']}: {error_msg}")
        
        # Return status codes and sample JSON
        self.log(f"\n📋 STATUS CODES AND SAMPLE JSON:")
        self.log(f"- Create Draft: 200 (returns id, status='draft', next_actions)")
        self.log(f"- Upload Media: 200 (returns media array with preview_urls)")
        self.log(f"- Submit Publish: 200 (returns status='published', detail_url)")
        self.log(f"- Get Detail: 200 (returns full listing with media URLs)")
        self.log(f"- Public Media: 200 (returns image file)")
        self.log(f"- Invalid Make: 422 (returns validation_errors with MAKE_NOT_FOUND)")
        self.log(f"- Insufficient Photos: 422 (returns validation_errors with MIN_PHOTOS)")
        self.log(f"- Draft Media Not Public: 404 (draft media protected from public access)")
        
        return self.tests_passed == self.tests_run

    def test_draft_media_not_public(self):
        """Test that draft media is not publicly accessible"""
        self.log("🚫 Testing draft media not public...")
        
        # Create a draft with media but don't publish
        draft_data = {
            "country": "DE",
            "category_key": "otomobil",
            "make_key": "bmw",
            "model_key": "3-serie",
            "year": 2020,
            "fuel_type": "benzin",
            "transmission": "manuel",
            "mileage_km": 50000,
            "price_eur": 25000,
            "condition": "ikinci-el",
            "power_hp": 184
        }
        
        # Create draft
        success, response = self.run_test(
            "Create Draft for Media Access Test",
            "POST",
            "/v1/listings/vehicle",
            200,
            data=draft_data
        )
        
        if not success:
            return False
            
        draft_listing_id = response.get('id')
        if not draft_listing_id:
            self.log("❌ No listing ID returned for draft media test")
            return False
        
        # Upload 3 images
        files = []
        for i in range(3):
            img_bytes = self.create_test_image(800, 600, (200, 100, 50))
            files.append(('files', (f'draft_test_{i+1}.jpg', img_bytes, 'image/jpeg')))
        
        upload_success, upload_response = self.run_test(
            "Upload Images for Draft Media Test",
            "POST",
            f"/v1/listings/vehicle/{draft_listing_id}/media",
            200,
            files=files
        )
        
        if not upload_success:
            return False
        
        # Get first media file name
        media = upload_response.get('media', [])
        if not media:
            self.log("❌ No media found in upload response")
            return False
            
        first_media = media[0]
        media_file = first_media.get('file', '')
        
        if not media_file:
            self.log("❌ No media file name found")
            return False
        
        # Try to access draft media via public URL (should fail)
        public_media_url = f"{self.base_url}/media/listings/{draft_listing_id}/{media_file}"
        
        self.log(f"   Testing draft media URL: {public_media_url}")
        
        try:
            response = requests.get(public_media_url)
            
            # Draft media should NOT be accessible (expecting 404)
            if response.status_code == 404:
                self.tests_passed += 1
                self.log(f"✅ PASSED - Draft Media Not Public - Status: {response.status_code}")
                self.log(f"   Draft media correctly protected from public access")
                return True
            else:
                self.log(f"❌ FAILED - Draft Media Not Public - Status: {response.status_code}")
                self.log(f"   Draft media should not be publicly accessible")
                self.failures.append({
                    'test': 'Draft Media Not Public',
                    'expected': 404,
                    'actual': response.status_code,
                    'endpoint': f"/media/listings/{draft_listing_id}/{media_file}"
                })
                return False
                
        except Exception as e:
            self.log(f"❌ FAILED - Draft Media Not Public - Exception: {str(e)}")
            self.failures.append({
                'test': 'Draft Media Not Public',
                'error': str(e),
                'endpoint': f"/media/listings/{draft_listing_id}/{media_file}"
            })
            return False
        finally:
            self.tests_run += 1

def main():
    tester = VehicleListingE2ETester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())