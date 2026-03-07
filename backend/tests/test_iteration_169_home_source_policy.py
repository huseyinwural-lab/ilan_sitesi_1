import os

import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")


def test_resolve_rejects_invalid_source_policy():
    response = requests.get(
        f"{BASE_URL}/api/site/content-layout/resolve",
        params={
            "country": "DE",
            "module": "global",
            "page_type": "home",
            "source_policy": "invalid_policy",
        },
        timeout=30,
    )
    assert response.status_code == 400, response.text
    assert response.json().get("detail") == "invalid_source_policy"


def test_content_builder_only_rejects_draft_preview():
    response = requests.get(
        f"{BASE_URL}/api/site/content-layout/resolve",
        params={
            "country": "DE",
            "module": "global",
            "page_type": "home",
            "source_policy": "content_builder_only",
            "layout_preview": "draft",
        },
        timeout=30,
    )
    assert response.status_code == 400, response.text
    assert response.json().get("detail") == "content_builder_only_requires_published_preview"
