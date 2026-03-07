#!/usr/bin/env python3
"""
Backend API Testing for Content Layout Resolve Endpoints
Turkish Review Request: Backend hızlı doğrulama
Base URL: https://page-builder-stable.preview.emergentagent.com

Kontroller:
1) GET /api/site/content-layout/resolve invalid source_policy
   source_policy=invalid_policy => 400 + detail=invalid_source_policy

2) GET /api/site/content-layout/resolve content_builder_only + draft
   page_type=home, source_policy=content_builder_only, layout_preview=draft => 400 + detail=content_builder_only_requires_published_preview

3) published resolve basic
   page_type=home, source_policy=content_builder_only, layout_preview=published(default) => 200/404/409 kabul, ama 500 olmamalı.

Kısa PASS/FAIL rapor ver.
"""

import requests
import sys
import json
from typing import Dict, Any

# Base URL from frontend environment
BASE_URL = "https://page-builder-stable.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

def test_content_layout_resolve_invalid_source_policy() -> Dict[str, Any]:
    """
    Test 1: GET /api/site/content-layout/resolve invalid source_policy
    Expected: source_policy=invalid_policy => 400 + detail=invalid_source_policy
    """
    print("🧪 TEST 1: Testing invalid source_policy...")
    
    url = f"{API_BASE}/site/content-layout/resolve"
    params = {
        "country": "DE",
        "module": "real_estate", 
        "page_type": "home",
        "source_policy": "invalid_policy"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        result = {
            "test_name": "Invalid Source Policy",
            "url": url,
            "params": params,
            "status_code": response.status_code,
            "response_body": {},
            "passed": False,
            "reason": ""
        }
        
        try:
            result["response_body"] = response.json()
        except:
            result["response_body"] = {"raw_text": response.text[:500]}
        
        # Check expected: 400 status + detail=invalid_source_policy
        if response.status_code == 400:
            detail = result["response_body"].get("detail", "")
            if detail == "invalid_source_policy":
                result["passed"] = True
                result["reason"] = "✅ Correctly returned 400 with detail=invalid_source_policy"
            else:
                result["reason"] = f"❌ Wrong detail message. Expected 'invalid_source_policy', got '{detail}'"
        else:
            result["reason"] = f"❌ Wrong status code. Expected 400, got {response.status_code}"
            
        return result
        
    except Exception as e:
        return {
            "test_name": "Invalid Source Policy",
            "url": url,
            "params": params,
            "status_code": "ERROR",
            "response_body": {"error": str(e)},
            "passed": False,
            "reason": f"❌ Request failed: {str(e)}"
        }


def test_content_layout_resolve_content_builder_draft() -> Dict[str, Any]:
    """
    Test 2: GET /api/site/content-layout/resolve content_builder_only + draft
    Expected: page_type=home, source_policy=content_builder_only, layout_preview=draft => 400 + detail=content_builder_only_requires_published_preview
    """
    print("🧪 TEST 2: Testing content_builder_only with draft preview...")
    
    url = f"{API_BASE}/site/content-layout/resolve"
    params = {
        "country": "DE",
        "module": "real_estate",
        "page_type": "home", 
        "source_policy": "content_builder_only",
        "layout_preview": "draft"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        result = {
            "test_name": "Content Builder Only + Draft",
            "url": url,
            "params": params,
            "status_code": response.status_code,
            "response_body": {},
            "passed": False,
            "reason": ""
        }
        
        try:
            result["response_body"] = response.json()
        except:
            result["response_body"] = {"raw_text": response.text[:500]}
        
        # Check expected: 400 status + detail=content_builder_only_requires_published_preview
        if response.status_code == 400:
            detail = result["response_body"].get("detail", "")
            if detail == "content_builder_only_requires_published_preview":
                result["passed"] = True
                result["reason"] = "✅ Correctly returned 400 with detail=content_builder_only_requires_published_preview"
            else:
                result["reason"] = f"❌ Wrong detail message. Expected 'content_builder_only_requires_published_preview', got '{detail}'"
        else:
            result["reason"] = f"❌ Wrong status code. Expected 400, got {response.status_code}"
            
        return result
        
    except Exception as e:
        return {
            "test_name": "Content Builder Only + Draft", 
            "url": url,
            "params": params,
            "status_code": "ERROR",
            "response_body": {"error": str(e)},
            "passed": False,
            "reason": f"❌ Request failed: {str(e)}"
        }


def test_content_layout_resolve_published_basic() -> Dict[str, Any]:
    """
    Test 3: published resolve basic
    Expected: page_type=home, source_policy=content_builder_only, layout_preview=published(default) => 200/404/409 kabul, ama 500 olmamalı.
    """
    print("🧪 TEST 3: Testing published resolve basic...")
    
    url = f"{API_BASE}/site/content-layout/resolve"
    params = {
        "country": "DE", 
        "module": "real_estate",
        "page_type": "home",
        "source_policy": "content_builder_only"
        # layout_preview=published is default, so we don't need to specify it
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        result = {
            "test_name": "Published Resolve Basic",
            "url": url,
            "params": params,
            "status_code": response.status_code,
            "response_body": {},
            "passed": False,
            "reason": ""
        }
        
        try:
            result["response_body"] = response.json()
        except:
            result["response_body"] = {"raw_text": response.text[:500]}
        
        # Check expected: 200/404/409 acceptable, but NOT 500
        acceptable_codes = [200, 404, 409]
        if response.status_code in acceptable_codes:
            result["passed"] = True
            result["reason"] = f"✅ Correctly returned acceptable status code {response.status_code} (200/404/409 kabul)"
        elif response.status_code == 500:
            result["reason"] = f"❌ Server error (500) - this should not happen!"
        else:
            result["reason"] = f"❌ Unexpected status code {response.status_code}. Expected 200/404/409, got {response.status_code}"
            
        return result
        
    except Exception as e:
        return {
            "test_name": "Published Resolve Basic",
            "url": url, 
            "params": params,
            "status_code": "ERROR",
            "response_body": {"error": str(e)},
            "passed": False,
            "reason": f"❌ Request failed: {str(e)}"
        }


def run_backend_tests() -> None:
    """Run all backend tests and generate report"""
    print("=" * 80)
    print("🚀 BACKEND API TESTING - Content Layout Resolve")
    print(f"📍 Base URL: {BASE_URL}")
    print("=" * 80)
    
    # Run tests
    test_results = []
    
    test_results.append(test_content_layout_resolve_invalid_source_policy())
    print()
    
    test_results.append(test_content_layout_resolve_content_builder_draft())
    print()
    
    test_results.append(test_content_layout_resolve_published_basic())
    print()
    
    # Generate summary report
    print("=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed_count = 0
    total_count = len(test_results)
    
    for i, result in enumerate(test_results, 1):
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"Test {i}: {result['test_name']} - {status}")
        print(f"   Status: {result['status_code']}")
        print(f"   Reason: {result['reason']}")
        if not result["passed"]:
            print(f"   URL: {result['url']}")
            print(f"   Params: {result['params']}")
            if result["response_body"]:
                print(f"   Response: {json.dumps(result['response_body'], indent=2)[:300]}...")
        print()
        
        if result["passed"]:
            passed_count += 1
    
    print("=" * 80)
    print(f"🎯 FINAL RESULT: {passed_count}/{total_count} TESTS PASSED")
    
    if passed_count == total_count:
        print("🎉 ALL TESTS PASSED! Backend API validation successful.")
        print("✅ KISA PASS/FAIL RAPOR: PASS - Tüm backend kontrolleri başarılı")
    else:
        print("⚠️  SOME TESTS FAILED! Backend API validation needs attention.")
        print("❌ KISA PASS/FAIL RAPOR: FAIL - Bazı backend kontrolleri başarısız")
    
    print("=" * 80)
    
    # Return success/failure for script exit code
    return passed_count == total_count


if __name__ == "__main__":
    success = run_backend_tests()
    sys.exit(0 if success else 1)