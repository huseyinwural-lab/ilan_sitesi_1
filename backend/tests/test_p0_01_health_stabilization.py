"""
P0-01 Health Stabilization Tests

Tests health endpoint contracts:
- /api/health/db always returns HTTP 200 (never 503)
- status field: ok|degraded
- db_status field: ok|fail
- reason field: includes migration_required
- /api/health/migrations endpoint working
- Concurrency stress test (20 workers)
"""

import pytest
import requests
import os
import time
import json
import concurrent.futures
from datetime import datetime

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


class TestHealthDbContract:
    """Tests /api/health/db endpoint contract"""

    def test_health_db_returns_200_always(self):
        """Verify /api/health/db always returns HTTP 200 (never 503)"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        
        # CRITICAL: Must always be 200, never 503
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: /api/health/db returned HTTP 200")

    def test_health_db_status_field_values(self):
        """Verify status field is either 'ok' or 'degraded'"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        status = data.get("status")
        
        assert status in ("ok", "degraded"), f"status must be 'ok' or 'degraded', got '{status}'"
        print(f"PASS: status field = '{status}' (valid)")

    def test_health_db_status_field_present(self):
        """Verify db_status field is present and valid"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        db_status = data.get("db_status")
        
        assert db_status in ("ok", "fail"), f"db_status must be 'ok' or 'fail', got '{db_status}'"
        print(f"PASS: db_status field = '{db_status}' (valid)")

    def test_health_db_response_structure(self):
        """Verify response includes all expected fields"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        
        # Required fields
        required_fields = [
            "status",
            "database",
            "db_status",
            "migration_state",
            "db_timeout_ms",
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  - {field}: {data.get(field)}")
        
        # Optional fields (should be present in normal operation)
        optional_fields = ["target", "db_latency_ms", "migration_head", "migration_current", "last_migration_check_at"]
        for field in optional_fields:
            if field in data:
                print(f"  - {field}: {data.get(field)}")
        
        print("PASS: All required fields present")

    def test_health_db_timeout_config(self):
        """Verify 500ms timeout is configured"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        timeout_ms = data.get("db_timeout_ms")
        
        assert timeout_ms == 500, f"db_timeout_ms must be 500, got {timeout_ms}"
        print(f"PASS: db_timeout_ms = 500 (correct)")

    def test_health_db_reason_field_when_degraded(self):
        """Verify reason field is present when status is degraded"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        status = data.get("status")
        reason = data.get("reason")
        
        if status == "degraded":
            assert reason is not None, "reason field must be present when status is degraded"
            print(f"PASS: status=degraded, reason='{reason}'")
        else:
            print(f"PASS: status=ok (no degraded scenario to test)")


class TestHealthMigrations:
    """Tests /api/health/migrations endpoint"""

    def test_health_migrations_returns_200(self):
        """Verify /api/health/migrations returns HTTP 200"""
        response = requests.get(f"{BASE_URL}/api/health/migrations", timeout=10)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"PASS: /api/health/migrations returned HTTP 200")

    def test_health_migrations_response_structure(self):
        """Verify migration endpoint response structure"""
        response = requests.get(f"{BASE_URL}/api/health/migrations", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        
        required_fields = [
            "status",
            "database",
            "migration_state",
            "migration_required",
            "db_status",
        ]
        
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
            print(f"  - {field}: {data.get(field)}")
        
        print("PASS: All required fields present")

    def test_health_migrations_migration_required_flag(self):
        """Verify migration_required field is boolean or null"""
        response = requests.get(f"{BASE_URL}/api/health/migrations", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        migration_required = data.get("migration_required")
        
        assert migration_required in (True, False, None), f"migration_required must be bool or null, got {migration_required}"
        print(f"PASS: migration_required = {migration_required}")

    def test_health_migrations_state_values(self):
        """Verify migration_state is valid"""
        response = requests.get(f"{BASE_URL}/api/health/migrations", timeout=10)
        assert response.status_code == 200
        
        data = response.json()
        migration_state = data.get("migration_state")
        
        valid_states = ("ok", "migration_required", "unknown")
        assert migration_state in valid_states, f"migration_state must be one of {valid_states}, got '{migration_state}'"
        print(f"PASS: migration_state = '{migration_state}'")


class TestHealthContracts15MinLoop:
    """Verify 15 minute loop test results"""

    def test_15min_loop_result_exists(self):
        """Verify 15 minute loop test was run and results exist"""
        report_path = "/app/test_reports/p0_01_health_15m.json"
        
        assert os.path.exists(report_path), f"15min loop report not found: {report_path}"
        
        with open(report_path, "r") as f:
            data = json.load(f)
        
        print(f"15min loop report loaded:")
        print(f"  - total_requests: {data.get('total_requests')}")
        print(f"  - duration_sec: {data.get('duration_sec')}")
        print("PASS: Report file exists and is valid JSON")

    def test_15min_loop_no_503_errors(self):
        """Verify count_503=0 in 15 minute loop results"""
        report_path = "/app/test_reports/p0_01_health_15m.json"
        
        with open(report_path, "r") as f:
            data = json.load(f)
        
        count_503 = data.get("count_503", -1)
        
        assert count_503 == 0, f"Expected count_503=0, got {count_503}"
        print(f"PASS: count_503 = 0 (no 503 errors in 15 minute loop)")

    def test_15min_loop_http_200_count(self):
        """Verify all requests returned HTTP 200"""
        report_path = "/app/test_reports/p0_01_health_15m.json"
        
        with open(report_path, "r") as f:
            data = json.load(f)
        
        http_code_counts = data.get("http_code_counts", {})
        total_requests = data.get("total_requests", 0)
        count_200 = http_code_counts.get("200", 0)
        
        assert count_200 == total_requests, f"Expected all {total_requests} requests to be 200, got {count_200}"
        print(f"PASS: All {total_requests} requests returned HTTP 200")

    def test_15min_loop_duration(self):
        """Verify loop ran for approximately 15 minutes"""
        report_path = "/app/test_reports/p0_01_health_15m.json"
        
        with open(report_path, "r") as f:
            data = json.load(f)
        
        duration_sec = data.get("duration_sec", 0)
        
        # Allow +/- 60 seconds tolerance
        assert 840 <= duration_sec <= 960, f"Expected ~900 sec duration, got {duration_sec}"
        print(f"PASS: Duration = {duration_sec}s (~15 minutes)")

    def test_15min_loop_latency_metrics(self):
        """Verify latency metrics are reasonable"""
        report_path = "/app/test_reports/p0_01_health_15m.json"
        
        with open(report_path, "r") as f:
            data = json.load(f)
        
        p95_ms = data.get("p95_ms", 0)
        avg_ms = data.get("avg_ms", 0)
        
        # p95 should be < 500ms (the timeout)
        assert p95_ms < 500, f"p95 latency {p95_ms}ms exceeds timeout threshold"
        print(f"PASS: p95_ms = {p95_ms}ms (below timeout)")
        print(f"      avg_ms = {avg_ms}ms")


class TestHealthConcurrency:
    """Concurrency stress test with 20 workers"""

    def test_concurrent_health_db_20_workers(self):
        """Verify no 503 under concurrent load (20 workers)"""
        num_workers = 20
        requests_per_worker = 10
        total_requests = num_workers * requests_per_worker
        
        results = []
        errors = []
        count_503 = 0
        
        def make_request(worker_id):
            worker_results = []
            for i in range(requests_per_worker):
                try:
                    start = time.perf_counter()
                    response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
                    latency_ms = (time.perf_counter() - start) * 1000
                    worker_results.append({
                        "worker": worker_id,
                        "request": i,
                        "status_code": response.status_code,
                        "latency_ms": latency_ms,
                    })
                except Exception as e:
                    worker_results.append({
                        "worker": worker_id,
                        "request": i,
                        "error": str(e),
                    })
            return worker_results
        
        print(f"Starting concurrent test: {num_workers} workers x {requests_per_worker} requests = {total_requests} total")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_workers)]
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
        
        # Count results
        for r in results:
            if "error" in r:
                errors.append(r)
            elif r.get("status_code") == 503:
                count_503 += 1
        
        # Calculate statistics
        latencies = [r.get("latency_ms", 0) for r in results if "latency_ms" in r]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        max_latency = max(latencies) if latencies else 0
        
        print(f"Results:")
        print(f"  - Total requests: {len(results)}")
        print(f"  - count_503: {count_503}")
        print(f"  - Errors: {len(errors)}")
        print(f"  - Avg latency: {avg_latency:.2f}ms")
        print(f"  - Max latency: {max_latency:.2f}ms")
        
        # Assert no 503 errors
        assert count_503 == 0, f"Expected count_503=0, got {count_503}"
        print("PASS: No 503 errors under concurrent load")

    def test_concurrent_health_migrations_10_workers(self):
        """Verify /api/health/migrations handles concurrent load"""
        num_workers = 10
        requests_per_worker = 5
        
        results = []
        count_503 = 0
        
        def make_request(worker_id):
            worker_results = []
            for i in range(requests_per_worker):
                try:
                    response = requests.get(f"{BASE_URL}/api/health/migrations", timeout=10)
                    worker_results.append({
                        "worker": worker_id,
                        "status_code": response.status_code,
                    })
                except Exception as e:
                    worker_results.append({
                        "worker": worker_id,
                        "error": str(e),
                    })
            return worker_results
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_workers)]
            for future in concurrent.futures.as_completed(futures):
                results.extend(future.result())
        
        for r in results:
            if r.get("status_code") == 503:
                count_503 += 1
        
        print(f"Results: {len(results)} requests, count_503={count_503}")
        assert count_503 == 0, f"Expected count_503=0, got {count_503}"
        print("PASS: No 503 errors on /api/health/migrations")


class TestHealthDbMigrationRequired:
    """Test migration_required scenario in /api/health/db"""

    def test_migration_required_returns_200_degraded(self):
        """When migration_required, /api/health/db returns 200 + status=degraded + reason=migration_required"""
        response = requests.get(f"{BASE_URL}/api/health/db", timeout=10)
        
        # Must be 200 even in migration_required state
        assert response.status_code == 200
        
        data = response.json()
        migration_state = data.get("migration_state")
        status = data.get("status")
        reason = data.get("reason")
        
        if migration_state == "migration_required":
            assert status == "degraded", f"When migration_required, status must be 'degraded', got '{status}'"
            assert reason == "migration_required", f"When migration_required, reason must be 'migration_required', got '{reason}'"
            print(f"PASS: migration_required scenario - status=degraded, reason=migration_required")
        else:
            print(f"INFO: Current migration_state is '{migration_state}' (not migration_required)")


class TestHealth24HProgress:
    """Check 24h monitoring progress"""

    def test_24h_progress_file_exists(self):
        """Verify 24h monitoring is running"""
        progress_path = "/app/test_reports/p0_01_health_24h.progress"
        
        if os.path.exists(progress_path):
            with open(progress_path, "r") as f:
                data = json.load(f)
            
            print(f"24h monitoring progress:")
            print(f"  - elapsed_sec: {data.get('elapsed_sec')}")
            print(f"  - samples: {data.get('samples')}")
            print(f"  - count_503: {data.get('count_503')}")
            print(f"  - errors: {data.get('errors')}")
            
            count_503 = data.get("count_503", -1)
            assert count_503 == 0, f"24h monitoring shows count_503={count_503}"
            print("PASS: 24h monitoring shows count_503=0")
        else:
            pytest.skip("24h progress file not found (monitoring may not be running)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
