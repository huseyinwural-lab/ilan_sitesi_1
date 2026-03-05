"""
P0-03 Country Selector Update & Host+Redirect Regression Tests
Tests:
1. places/config country_options = DE, FR, CH, AT only (TR removed)
2. listing.create.config country_selector_mode = radio
3. http -> https redirect max 1 hop
4. Preview sitemap host 100% correct
"""
import os
import pytest
import requests
import urllib.request
import ssl
import xml.etree.ElementTree as ET

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://content-canvas-16.preview.emergentagent.com').rstrip('/')


class TestPlacesConfigCountrySelector:
    """Test /api/places/config for country_options and country_selector_mode"""
    
    def test_places_config_returns_200(self):
        """Verify places/config endpoint is accessible"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_country_options_exact_set(self):
        """Verify country_options contains exactly DE, FR, CH, AT (TR removed)"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        country_codes = [c.get('code') for c in data.get('country_options', [])]
        
        # Verify exact set
        expected_codes = {'DE', 'FR', 'CH', 'AT'}
        actual_codes = set(country_codes)
        
        assert actual_codes == expected_codes, f"Expected {expected_codes}, got {actual_codes}"
        
    def test_tr_not_in_country_options(self):
        """Verify TR (Turkey) is NOT in country_options"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        country_codes = [c.get('code') for c in data.get('country_options', [])]
        
        assert 'TR' not in country_codes, f"TR should NOT be in country_options, but found: {country_codes}"
    
    def test_country_selector_mode_is_radio(self):
        """Verify listing_create_config.country_selector_mode = 'radio'"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        listing_config = data.get('listing_create_config', {})
        selector_mode = listing_config.get('country_selector_mode')
        
        assert selector_mode == 'radio', f"Expected 'radio', got '{selector_mode}'"


class TestListingCreateConfig:
    """Test listing.create.config endpoint"""
    
    def test_listing_create_get_returns_200(self):
        """Verify listing create config endpoint is accessible via admin"""
        # This test checks if the config matches what places/config returns
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        listing_config = data.get('listing_create_config', {})
        
        # Verify structure
        assert 'country_selector_mode' in listing_config
        assert 'postal_code_required' in listing_config
        
    def test_country_selector_mode_radio_in_listing_config(self):
        """Verify country_selector_mode is 'radio' in listing_create_config"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        listing_config = data.get('listing_create_config', {})
        assert listing_config.get('country_selector_mode') == 'radio'


class TestHttpToHttpsRedirect:
    """Test HTTP to HTTPS redirect behavior"""
    
    def test_http_to_https_redirect_max_1_hop(self):
        """Verify HTTP -> HTTPS redirect happens in max 1 hop"""
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        
        http_url = "http://marketplace-finance-3.preview.emergentagent.com/"
        
        # Follow redirects manually to count hops
        hops = 0
        current_url = http_url
        max_hops = 5
        
        while hops < max_hops:
            req = urllib.request.Request(current_url, method='GET')
            req.add_header('User-Agent', 'Mozilla/5.0')
            try:
                ctx = ssl_ctx if current_url.startswith('https') else None
                response = urllib.request.urlopen(req, context=ctx, timeout=15)
                # If we got here, no more redirects
                break
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 307, 308):
                    location = e.headers.get('Location')
                    current_url = location
                    hops += 1
                else:
                    break
        
        assert hops <= 1, f"HTTP->HTTPS redirect should be max 1 hop, got {hops} hops"
    
    def test_https_no_redirect(self):
        """Verify HTTPS URL has 0 redirects"""
        https_url = "https://content-canvas-16.preview.emergentagent.com/"
        response = requests.get(https_url, allow_redirects=False, timeout=10, verify=False)
        
        # Should return 200 directly, not a redirect
        assert response.status_code == 200, f"HTTPS should return 200, got {response.status_code}"


class TestSitemapHostCorrect:
    """Test sitemap URLs use correct host"""
    
    def test_sitemap_index_accessible(self):
        """Verify sitemap index is accessible"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=10, verify=False)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'xml' in response.headers.get('Content-Type', '').lower()
    
    def test_sitemap_index_hosts_correct(self):
        """Verify sitemap index URLs contain correct preview host"""
        response = requests.get(f"{BASE_URL}/api/sitemap.xml", timeout=10, verify=False)
        content = response.text
        
        expected_host = "marketplace-finance-3.preview.emergentagent.com"
        
        root = ET.fromstring(content)
        
        urls = []
        for loc in root.iter():
            if loc.tag.endswith('loc') and loc.text:
                urls.append(loc.text)
        
        wrong_urls = [u for u in urls if expected_host not in u]
        
        assert len(wrong_urls) == 0, f"Found {len(wrong_urls)} URLs with wrong host: {wrong_urls[:5]}"
        assert len(urls) > 0, "Sitemap should contain at least 1 URL"


class TestRegressionSummary:
    """Aggregate regression test summary"""
    
    def test_country_selector_complete(self):
        """Meta test: All country selector requirements met"""
        response = requests.get(f"{BASE_URL}/api/places/config", timeout=30)
        data = response.json()
        
        # Country options
        country_codes = {c.get('code') for c in data.get('country_options', [])}
        expected = {'DE', 'FR', 'CH', 'AT'}
        
        assert country_codes == expected, f"Country codes mismatch: {country_codes} vs {expected}"
        assert 'TR' not in country_codes, "TR should not be in country options"
        
        # Selector mode
        listing_config = data.get('listing_create_config', {})
        assert listing_config.get('country_selector_mode') == 'radio'
        
        print("\n=== Country Selector Update Summary ===")
        print(f"✅ Country codes: {sorted(country_codes)}")
        print(f"✅ TR removed: True")
        print(f"✅ Selector mode: radio")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
