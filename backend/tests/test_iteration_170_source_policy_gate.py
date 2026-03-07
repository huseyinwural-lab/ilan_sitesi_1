from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_home_page_source_policy_gate_present():
    content = _read("/app/frontend/src/pages/public/HomePageRefreshed.js")
    assert "sourcePolicy: 'content_builder_only'" in content
    assert "allowDraftPreview: false" in content


def test_search_page_source_policy_gate_present():
    content = _read("/app/frontend/src/pages/public/SearchPage.js")
    assert "sourcePolicy: 'content_builder_only'" in content
    assert "allowDraftPreview: false" in content


def test_detail_page_source_policy_gate_present():
    content = _read("/app/frontend/src/pages/public/DetailPage.js")
    assert "sourcePolicy: 'content_builder_only'" in content
    assert "allowDraftPreview: false" in content
    assert "listing-detail-layout-empty-state" in content


def test_resolve_api_enforces_source_policy_rules():
    content = _read("/app/backend/app/routers/layout_builder_routes.py")
    assert "invalid_source_policy" in content
    assert "content_builder_only_requires_published_preview" in content
    assert "home_content_builder_published_revision_required" in content
