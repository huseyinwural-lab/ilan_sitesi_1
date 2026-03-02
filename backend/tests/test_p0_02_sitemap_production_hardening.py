"""
P0-02 Sitemap Production Hardening Tests
-----------------------------------------
Goal: Verify hardcoded base URL removed, single host source, deterministic canonical,
sitemap coverage (home/category/listing/info), prod+preview host correctness.
"""
import pytest
import requests
import os
import re
import time
from xml.etree import ElementTree as ET

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
PREVIEW_HOST = "marketplace-finance-3.preview.emergentagent.com"
PROD_HOST = "www.annoncia.com"
DEFAULT_TIMEOUT = 30

def retry_get(url, timeout=DEFAULT_TIMEOUT, retries=3):
    """GET request with retry logic for transient network issues"""
    for attempt in range(retries):
        try:
            return requests.get(url, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            raise


class TestSitemapEndpointsStatus:
    """Verify all sitemap endpoints return 200 + XML content"""

    def test_sitemap_index_returns_200_xml(self):
        """GET /api/sitemap.xml returns 200 with XML content"""
        response = retry_get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "xml" in response.headers.get("content-type", "").lower(), "Expected XML content-type"
        assert "<?xml" in response.text[:50], "Response should be valid XML"
        print(f"PASS: /api/sitemap.xml -> 200 XML")

    def test_sitemap_core_returns_200_xml(self):
        """GET /api/sitemaps/core.xml returns 200 with XML urlset"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/core.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "urlset" in response.text, "Response should contain <urlset>"
        print(f"PASS: /api/sitemaps/core.xml -> 200 XML")

    def test_sitemap_categories_returns_200_xml(self):
        """GET /api/sitemaps/categories.xml returns 200 with XML urlset"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/categories.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "urlset" in response.text, "Response should contain <urlset>"
        print(f"PASS: /api/sitemaps/categories.xml -> 200 XML")

    def test_sitemap_listings_returns_200_xml(self):
        """GET /api/sitemaps/listings.xml returns 200 with XML urlset"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/listings.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "urlset" in response.text, "Response should contain <urlset>"
        print(f"PASS: /api/sitemaps/listings.xml -> 200 XML")

    def test_sitemap_info_returns_200_xml(self):
        """GET /api/sitemaps/info.xml returns 200 with XML urlset"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/info.xml")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "urlset" in response.text, "Response should contain <urlset>"
        print(f"PASS: /api/sitemaps/info.xml -> 200 XML")

    def test_sitemap_invalid_section_returns_404(self):
        """GET /api/sitemaps/invalid.xml returns 404"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/invalid.xml")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"PASS: /api/sitemaps/invalid.xml -> 404")


class TestSitemapHostResolution:
    """Verify host is resolved from request/env, not hardcoded"""

    def test_sitemap_index_uses_preview_host(self):
        """Sitemap index should use preview host from headers"""
        response = retry_get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        # Check response headers for base URL source
        base_source = response.headers.get("X-Sitemap-Base-Source", "")
        base_url_header = response.headers.get("X-Sitemap-Base-Url", "")
        
        # All URLs in response should use preview host
        assert PREVIEW_HOST in response.text, f"Expected {PREVIEW_HOST} in sitemap XML"
        assert "localhost" not in response.text.lower(), "No localhost should be in sitemap"
        assert "127.0.0.1" not in response.text, "No 127.0.0.1 should be in sitemap"
        print(f"PASS: Sitemap index uses correct host ({PREVIEW_HOST})")
        print(f"  Base-Source: {base_source}, Base-Url: {base_url_header}")

    def test_sitemap_section_uses_preview_host(self):
        """Sitemap sections should use preview host"""
        for section in ["core", "categories", "listings", "info"]:
            response = retry_get(f"{BASE_URL}/api/sitemaps/{section}.xml")
            assert response.status_code == 200
            
            # Check headers
            base_source = response.headers.get("X-Sitemap-Base-Source", "")
            base_url_header = response.headers.get("X-Sitemap-Base-Url", "")
            
            # Verify host in URLs
            urls = re.findall(r'<loc>([^<]+)</loc>', response.text)
            wrong_hosts = [u for u in urls if PREVIEW_HOST not in u]
            
            assert len(wrong_hosts) == 0, f"Wrong hosts found in {section}.xml: {wrong_hosts[:5]}"
            print(f"PASS: {section}.xml uses correct host ({len(urls)} URLs)")


class TestSitemapContentCoverage:
    """Verify sitemap includes required page types"""

    def test_core_sitemap_contains_home_and_static(self):
        """core.xml should contain home, search, trust, kurumsal, seo"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/core.xml")
        assert response.status_code == 200
        
        required_paths = ["/", "/search", "/trust", "/kurumsal", "/seo"]
        for path in required_paths:
            expected = f"https://{PREVIEW_HOST}{path}"
            # Handle trailing slash edge case for home
            if path == "/":
                assert f"https://{PREVIEW_HOST}/</loc>" in response.text or f"https://{PREVIEW_HOST}</loc>" in response.text, f"Missing home path in core.xml"
            else:
                assert expected in response.text, f"Missing {expected} in core.xml"
        
        print(f"PASS: core.xml contains required static paths: {required_paths}")

    def test_core_sitemap_contains_vehicle_paths(self):
        """core.xml should contain country-prefixed vasita paths"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/core.xml")
        assert response.status_code == 200
        
        # Check for DE/vasita pattern
        assert "/DE/vasita" in response.text or "/de/vasita" in response.text.lower(), "Missing /DE/vasita in core.xml"
        print(f"PASS: core.xml contains /DE/vasita paths")

    def test_categories_sitemap_contains_kategori_paths(self):
        """categories.xml should contain /kategori/ paths"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/categories.xml")
        assert response.status_code == 200
        
        assert "/kategori/" in response.text, "Missing /kategori/ paths in categories.xml"
        
        # Count category URLs
        urls = re.findall(r'<loc>[^<]*kategori[^<]*</loc>', response.text)
        assert len(urls) > 0, "No category URLs found"
        print(f"PASS: categories.xml contains {len(urls)} category URLs")

    def test_listings_sitemap_contains_ilan_paths(self):
        """listings.xml should contain /ilan/ paths for active listings"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/listings.xml")
        assert response.status_code == 200
        
        assert "/ilan/" in response.text, "Missing /ilan/ paths in listings.xml"
        
        # Count listing URLs
        urls = re.findall(r'<loc>[^<]*/ilan/[^<]*</loc>', response.text)
        assert len(urls) > 0, "No listing URLs found"
        print(f"PASS: listings.xml contains {len(urls)} listing URLs")

    def test_info_sitemap_contains_trust_kurumsal_seo(self):
        """info.xml should contain /trust, /kurumsal, /seo, /bilgi/ paths"""
        response = retry_get(f"{BASE_URL}/api/sitemaps/info.xml")
        assert response.status_code == 200
        
        required_paths = ["/trust", "/kurumsal", "/seo"]
        for path in required_paths:
            assert path in response.text, f"Missing {path} in info.xml"
        
        # Check for bilgi paths
        bilgi_urls = re.findall(r'<loc>[^<]*/bilgi/[^<]*</loc>', response.text)
        assert len(bilgi_urls) > 0, "No /bilgi/ URLs found in info.xml"
        
        print(f"PASS: info.xml contains trust/kurumsal/seo + {len(bilgi_urls)} bilgi URLs")


class TestSitemapTrailingSlashStandard:
    """Verify canonical URLs have correct trailing slash handling"""

    def test_no_trailing_slash_on_paths(self):
        """URLs should not have trailing slashes (except home)"""
        bad_trailing_slash = []
        
        for section in ["core", "categories", "listings", "info"]:
            response = retry_get(f"{BASE_URL}/api/sitemaps/{section}.xml")
            assert response.status_code == 200
            
            urls = re.findall(r'<loc>([^<]+)</loc>', response.text)
            for url in urls:
                # Home page can be "/" or without trailing slash
                if url.endswith("/") and url != f"https://{PREVIEW_HOST}/" and not url.endswith(".com/"):
                    bad_trailing_slash.append(url)
        
        if bad_trailing_slash:
            print(f"WARN: Found {len(bad_trailing_slash)} URLs with trailing slash: {bad_trailing_slash[:5]}")
        
        # Report but don't fail - this is informational
        assert len(bad_trailing_slash) == 0, f"Found {len(bad_trailing_slash)} bad trailing slashes"
        print(f"PASS: All URLs follow trailing slash standard")


class TestSitemapHostReportVerification:
    """Verify P0-02 report file shows no wrong hosts"""

    def test_p0_02_report_exists(self):
        """p0_02_sitemap_host_report.json should exist"""
        report_path = "/app/test_reports/p0_02_sitemap_host_report.json"
        assert os.path.exists(report_path), f"Report file missing: {report_path}"
        print(f"PASS: Report file exists at {report_path}")

    def test_p0_02_report_preview_wrong_host_zero(self):
        """Preview host should have wrong_host_count = 0"""
        import json
        report_path = "/app/test_reports/p0_02_sitemap_host_report.json"
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        preview = report.get("preview", {})
        wrong_host = preview.get("wrong_host_count", -1)
        
        assert wrong_host == 0, f"Preview wrong_host_count should be 0, got {wrong_host}"
        print(f"PASS: Preview wrong_host_count = 0")

    def test_p0_02_report_prod_wrong_host_zero(self):
        """Prod host should have wrong_host_count = 0"""
        import json
        report_path = "/app/test_reports/p0_02_sitemap_host_report.json"
        
        with open(report_path, "r") as f:
            report = json.load(f)
        
        prod = report.get("prod", {})
        wrong_host = prod.get("wrong_host_count", -1)
        
        assert wrong_host == 0, f"Prod wrong_host_count should be 0, got {wrong_host}"
        print(f"PASS: Prod wrong_host_count = 0")


class TestSitemapXMLValidity:
    """Verify XML is well-formed and parseable"""

    def test_sitemap_index_valid_xml(self):
        """Sitemap index should be valid XML"""
        response = retry_get(f"{BASE_URL}/api/sitemap.xml")
        assert response.status_code == 200
        
        try:
            root = ET.fromstring(response.text)
            assert root.tag.endswith("sitemapindex"), f"Expected sitemapindex, got {root.tag}"
            print(f"PASS: Sitemap index is valid XML with root <sitemapindex>")
        except ET.ParseError as e:
            pytest.fail(f"Invalid XML: {e}")

    def test_sitemap_sections_valid_xml(self):
        """All sitemap sections should be valid XML"""
        for section in ["core", "categories", "listings", "info"]:
            response = retry_get(f"{BASE_URL}/api/sitemaps/{section}.xml")
            assert response.status_code == 200
            
            try:
                root = ET.fromstring(response.text)
                assert root.tag.endswith("urlset"), f"Expected urlset in {section}, got {root.tag}"
                print(f"PASS: {section}.xml is valid XML with root <urlset>")
            except ET.ParseError as e:
                pytest.fail(f"Invalid XML in {section}.xml: {e}")


@pytest.fixture(scope="session")
def sitemap_data():
    """Preload sitemap data for all tests"""
    data = {}
    for section in ["index", "core", "categories", "listings", "info"]:
        if section == "index":
            url = f"{BASE_URL}/api/sitemap.xml"
        else:
            url = f"{BASE_URL}/api/sitemaps/{section}.xml"
        
        try:
            response = requests.get(url)
            data[section] = {
                "status": response.status_code,
                "text": response.text,
                "headers": dict(response.headers),
            }
        except Exception as e:
            data[section] = {"status": 0, "text": "", "error": str(e)}
    
    return data
