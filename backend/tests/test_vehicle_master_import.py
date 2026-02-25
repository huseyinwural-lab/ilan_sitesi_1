"""
Test Vehicle Master Data Import Module
- Tests JSON upload dry-run job creation
- Tests job status GET endpoint
- Tests invalid JSON upload validation (returns 400)
- RBAC check for masterdata_manager permission
"""
import pytest
import requests
import os
import json
import io

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    """Login as admin and get token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if response.status_code != 200:
        pytest.skip(f"Admin login failed: {response.status_code}")
    return response.json().get("access_token")


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


class TestVehicleMasterImportJobUpload:
    """Tests for /api/admin/vehicle-master-import/jobs/upload endpoint"""

    def test_upload_dry_run_job_create_valid_json(self, auth_headers):
        """Test dry-run job creation with valid JSON file"""
        valid_records = [
            {
                "make_name": "TEST_BMW",
                "model_name": "TEST_X5",
                "year": 2024,
                "name": "xDrive40i",
            },
            {
                "make_name": "TEST_Audi",
                "model_name": "TEST_A4",
                "year": 2023,
                "name": "Quattro",
            },
        ]
        json_content = json.dumps(valid_records)
        files = {
            "file": ("test_vehicles.json", io.BytesIO(json_content.encode("utf-8")), "application/json")
        }
        data = {"dry_run": "true"}

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        # Should create job with status queued
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        job_data = response.json()
        assert "job" in job_data
        job = job_data["job"]
        assert "id" in job
        assert job["source"] == "upload"
        assert job["dry_run"] is True
        assert job["status"] in ["queued", "processing", "completed"]
        print(f"✅ Dry-run job created successfully: {job['id']}")
        return job["id"]

    def test_upload_invalid_json_format_returns_400(self, auth_headers):
        """Test that uploading invalid (non-array) JSON returns 400"""
        invalid_json = {"not": "an_array"}
        json_content = json.dumps(invalid_json)
        files = {
            "file": ("invalid.json", io.BytesIO(json_content.encode("utf-8")), "application/json")
        }
        data = {"dry_run": "true"}

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400, f"Expected 400 for non-array JSON, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", "")
        assert "array" in str(detail).lower() or "JSON" in str(detail), f"Error should mention array format: {detail}"
        print(f"✅ Invalid JSON format correctly rejected with 400: {detail}")

    def test_upload_malformed_json_returns_400(self, auth_headers):
        """Test that uploading malformed JSON returns 400"""
        malformed_json = b"{ not valid json"
        files = {
            "file": ("malformed.json", io.BytesIO(malformed_json), "application/json")
        }
        data = {"dry_run": "false"}

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400, f"Expected 400 for malformed JSON, got {response.status_code}: {response.text}"
        print(f"✅ Malformed JSON correctly rejected with 400")

    def test_upload_validation_errors_returns_400(self, auth_headers):
        """Test that uploading records with missing required fields returns 400"""
        # Records missing required fields (make_name, model_name, year, name)
        invalid_records = [
            {"model_name": "X5", "year": 2024},  # Missing make_name and name
            {"make_name": "BMW"},  # Missing model_name, year, name
        ]
        json_content = json.dumps(invalid_records)
        files = {
            "file": ("invalid_records.json", io.BytesIO(json_content.encode("utf-8")), "application/json")
        }
        data = {"dry_run": "true"}

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        # Should return 400 with validation errors
        assert response.status_code == 400, f"Expected 400 for invalid records, got {response.status_code}: {response.text}"
        detail = response.json().get("detail", {})
        # Check for validation_errors structure
        if isinstance(detail, dict):
            assert "validation_errors" in detail or "validation_error_count" in detail, f"Expected validation_errors in detail: {detail}"
            print(f"✅ Validation errors correctly returned: {detail.get('validation_error_count', 0)} errors")
        else:
            print(f"✅ Validation rejected with 400: {detail}")

    def test_upload_empty_file_returns_400(self, auth_headers):
        """Test that uploading empty file returns 400"""
        files = {
            "file": ("empty.json", io.BytesIO(b""), "application/json")
        }
        data = {"dry_run": "true"}

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        assert response.status_code == 400, f"Expected 400 for empty file, got {response.status_code}: {response.text}"
        print(f"✅ Empty file correctly rejected with 400")


class TestVehicleMasterImportJobStatus:
    """Tests for GET /api/admin/vehicle-master-import/jobs/{id} endpoint"""

    def test_get_job_status_valid_id(self, auth_headers):
        """Test getting job status with valid job ID - first create a job, then get status"""
        # Create a dry-run job first
        valid_records = [
            {
                "make_name": "TEST_STATUS_BMW",
                "model_name": "TEST_STATUS_X3",
                "year": 2024,
                "name": "xDrive30i",
            },
        ]
        json_content = json.dumps(valid_records)
        files = {
            "file": ("test_status.json", io.BytesIO(json_content.encode("utf-8")), "application/json")
        }
        data = {"dry_run": "true"}

        create_response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            headers=auth_headers,
            files=files,
            data=data,
        )

        if create_response.status_code != 200:
            pytest.skip(f"Could not create job for status test: {create_response.status_code}")

        job_id = create_response.json()["job"]["id"]

        # Now get the job status
        response = requests.get(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/{job_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        job_data = response.json()
        assert "job" in job_data
        job = job_data["job"]
        assert job["id"] == job_id
        assert "status" in job
        assert "dry_run" in job
        assert "source" in job
        assert "log_entries" in job
        print(f"✅ Job status retrieved successfully: status={job['status']}, dry_run={job['dry_run']}")

    def test_get_job_status_invalid_uuid(self, auth_headers):
        """Test getting job status with invalid UUID format"""
        response = requests.get(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/invalid-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 400, f"Expected 400 for invalid UUID, got {response.status_code}: {response.text}"
        print(f"✅ Invalid UUID correctly rejected with 400")

    def test_get_job_status_nonexistent_id(self, auth_headers):
        """Test getting job status with nonexistent UUID"""
        import uuid
        fake_uuid = str(uuid.uuid4())

        response = requests.get(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/{fake_uuid}",
            headers=auth_headers,
        )

        assert response.status_code == 404, f"Expected 404 for nonexistent job, got {response.status_code}: {response.text}"
        print(f"✅ Nonexistent job correctly returns 404")


class TestVehicleMasterImportJobList:
    """Tests for GET /api/admin/vehicle-master-import/jobs endpoint"""

    def test_list_jobs(self, auth_headers):
        """Test listing import jobs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs",
            headers=auth_headers,
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        print(f"✅ Job list retrieved: {len(data['items'])} jobs found")

        # Verify job structure if any exist
        if data["items"]:
            job = data["items"][0]
            assert "id" in job
            assert "status" in job
            assert "source" in job
            assert "dry_run" in job
            assert "created_at" in job
            print(f"✅ First job: id={job['id']}, status={job['status']}, source={job['source']}")


class TestVehicleMasterImportRBAC:
    """Tests for RBAC permissions on vehicle master import endpoints"""

    def test_upload_without_auth_returns_401(self):
        """Test that upload without authentication returns 401"""
        valid_records = [{"make_name": "Test", "model_name": "Test", "year": 2024, "name": "Test"}]
        json_content = json.dumps(valid_records)
        files = {
            "file": ("test.json", io.BytesIO(json_content.encode("utf-8")), "application/json")
        }

        response = requests.post(
            f"{BASE_URL}/api/admin/vehicle-master-import/jobs/upload",
            files=files,
            data={"dry_run": "true"},
        )

        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✅ Upload without auth correctly returns 401")

    def test_list_jobs_without_auth_returns_401(self):
        """Test that listing jobs without authentication returns 401"""
        response = requests.get(f"{BASE_URL}/api/admin/vehicle-master-import/jobs")

        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✅ List jobs without auth correctly returns 401")

    def test_get_job_without_auth_returns_401(self):
        """Test that getting job status without authentication returns 401"""
        import uuid
        fake_uuid = str(uuid.uuid4())

        response = requests.get(f"{BASE_URL}/api/admin/vehicle-master-import/jobs/{fake_uuid}")

        assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"
        print(f"✅ Get job without auth correctly returns 401")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
