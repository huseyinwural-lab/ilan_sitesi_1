import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
import requests
from sqlalchemy import and_, func, select

from app.database import AsyncSessionLocal
from app.domains.layout_builder.service import (
    bind_category_to_page,
    create_draft_revision,
    create_layout_page,
    publish_revision,
    unbind_category,
)
from app.models.category import Category
from app.models.layout_builder import (
    LayoutBinding,
    LayoutPage,
    LayoutPageType,
    LayoutRevision,
    LayoutRevisionStatus,
)


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "admin@platform.com"
ADMIN_PASSWORD = "Admin123!"


@pytest.fixture(scope="module")
def admin_token():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL not set")
    res = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    if res.status_code != 200:
        pytest.skip(f"Admin login failed: {res.status_code} {res.text[:200]}")
    return res.json().get("access_token")


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _first_category_id() -> str:
    response = requests.get(f"{BASE_URL}/api/categories?module=real_estate&country=DE")
    assert response.status_code == 200, response.text
    items = response.json()
    assert isinstance(items, list) and items, "categories must not be empty"
    return items[0]["id"]


class TestP74LayoutBuilderAPI:
    def test_component_schema_validation_and_key_conflict(self, admin_token):
        unique_key = f"test.component.{uuid.uuid4().hex[:10]}"

        invalid_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Invalid schema",
                "schema_json": {"type": "not-a-json-schema-type"},
                "is_active": True,
            },
        )
        assert invalid_res.status_code == 400, invalid_res.text

        create_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Listing Title",
                "schema_json": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}},
                    "required": ["title"],
                },
                "is_active": True,
            },
        )
        assert create_res.status_code == 200, create_res.text
        item = create_res.json().get("item", {})
        assert item.get("key") == unique_key

        conflict_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/components",
            headers=_headers(admin_token),
            json={
                "key": unique_key,
                "name": "Duplicated",
                "schema_json": {"type": "object", "properties": {}},
                "is_active": True,
            },
        )
        assert conflict_res.status_code == 409, conflict_res.text

    def test_layout_page_revision_publish_binding_and_resolve(self, admin_token):
        marker = uuid.uuid4().hex[:8]
        module_name = f"layout_mod_{marker}"
        category_id = _first_category_id()

        create_page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
        )
        assert create_page_res.status_code == 200, create_page_res.text
        default_page_id = create_page_res.json()["item"]["id"]

        dup_page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
        )
        assert dup_page_res.status_code == 409, dup_page_res.text

        draft_default_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{default_page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "row-default"}]}},
        )
        assert draft_default_res.status_code == 200, draft_default_res.text
        draft_default_id = draft_default_res.json()["item"]["id"]

        publish_default_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_default_id}/publish",
            headers=_headers(admin_token),
        )
        assert publish_default_res.status_code == 200, publish_default_res.text

        resolve_default_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
            },
        )
        assert resolve_default_res.status_code == 200, resolve_default_res.text
        assert resolve_default_res.json().get("source") in {"default", "cache"}

        create_category_page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "search_l1",
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
            },
        )
        assert create_category_page_res.status_code == 200, create_category_page_res.text
        category_page_id = create_category_page_res.json()["item"]["id"]

        draft_category_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{category_page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "row-category"}]}}
        )
        assert draft_category_res.status_code == 200, draft_category_res.text
        draft_category_id = draft_category_res.json()["item"]["id"]

        publish_category_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_category_id}/publish",
            headers=_headers(admin_token),
        )
        assert publish_category_res.status_code == 200, publish_category_res.text

        bind_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/bindings",
            headers=_headers(admin_token),
            json={
                "country": "DE",
                "module": module_name,
                "category_id": category_id,
                "layout_page_id": category_page_id,
            },
        )
        assert bind_res.status_code == 200, bind_res.text

        resolve_bound_res = requests.get(
            f"{BASE_URL}/api/site/content-layout/resolve",
            params={
                "country": "DE",
                "module": module_name,
                "page_type": "search_l1",
                "category_id": category_id,
            },
        )
        assert resolve_bound_res.status_code == 200, resolve_bound_res.text
        payload = resolve_bound_res.json()
        assert payload.get("revision", {}).get("layout_page_id") == category_page_id

        active_binding_res = requests.get(
            f"{BASE_URL}/api/admin/site/content-layout/bindings/active",
            headers=_headers(admin_token),
            params={"country": "DE", "module": module_name, "category_id": category_id},
        )
        assert active_binding_res.status_code == 200, active_binding_res.text
        assert active_binding_res.json().get("item", {}).get("layout_page_id") == category_page_id

    def test_publish_concurrency_single_winner(self, admin_token):
        marker = uuid.uuid4().hex[:8]
        module_name = f"layout_cc_{marker}"

        page_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages",
            headers=_headers(admin_token),
            json={
                "page_type": "home",
                "country": "DE",
                "module": module_name,
                "category_id": None,
            },
        )
        assert page_res.status_code == 200, page_res.text
        page_id = page_res.json()["item"]["id"]

        draft_res = requests.post(
            f"{BASE_URL}/api/admin/site/content-layout/pages/{page_id}/revisions/draft",
            headers=_headers(admin_token),
            json={"payload_json": {"rows": [{"id": "race"}]}}
        )
        assert draft_res.status_code == 200, draft_res.text
        draft_id = draft_res.json()["item"]["id"]

        def _publish_once():
            return requests.post(
                f"{BASE_URL}/api/admin/site/content-layout/revisions/{draft_id}/publish",
                headers=_headers(admin_token),
                timeout=20,
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            statuses = list(executor.map(lambda _: _publish_once(), [0, 1]))

        assert statuses.count(200) == 1, f"expected 1 success, got {statuses}"
        assert statuses.count(409) == 1, f"expected 1 conflict, got {statuses}"


@pytest.mark.asyncio
async def test_layout_builder_domain_services_unit_flow():
    marker = uuid.uuid4().hex[:8]
    module_name = f"svc_mod_{marker}"

    async with AsyncSessionLocal() as session:
        category_row = (
            await session.execute(select(Category).order_by(Category.created_at.desc()).limit(1))
        ).scalar_one_or_none()
        assert category_row is not None, "category seed missing"
        category_id = str(category_row.id)

        page = await create_layout_page(
            session,
            page_type=LayoutPageType.SEARCH_L2,
            country="DE",
            module=module_name,
            category_id=None,
            actor_user_id=None,
        )

        with pytest.raises(ValueError):
            await create_layout_page(
                session,
                page_type=LayoutPageType.SEARCH_L2,
                country="DE",
                module=module_name,
                category_id=None,
                actor_user_id=None,
            )
        await session.rollback()

        page = await create_layout_page(
            session,
            page_type=LayoutPageType.SEARCH_L2,
            country="DE",
            module=module_name,
            category_id=None,
            actor_user_id=None,
        )

        draft = await create_draft_revision(
            session,
            layout_page_id=str(page.id),
            payload_json={"rows": [{"id": "svc-row-1"}]},
            actor_user_id=None,
        )
        published = await publish_revision(
            session,
            revision_id=str(draft.id),
            actor_user_id=None,
        )
        assert published.status == LayoutRevisionStatus.PUBLISHED

        second_draft = await create_draft_revision(
            session,
            layout_page_id=str(page.id),
            payload_json={"rows": [{"id": "svc-row-2"}]},
            actor_user_id=None,
        )
        second_published = await publish_revision(
            session,
            revision_id=str(second_draft.id),
            actor_user_id=None,
        )
        assert second_published.status == LayoutRevisionStatus.PUBLISHED

        published_count_result = await session.execute(
            select(func.count())
            .select_from(LayoutRevision)
            .where(
                and_(
                    LayoutRevision.layout_page_id == page.id,
                    LayoutRevision.status == LayoutRevisionStatus.PUBLISHED,
                )
            )
        )
        assert int(published_count_result.scalar() or 0) == 1

        bound = await bind_category_to_page(
            session,
            country="DE",
            module=module_name,
            category_id=category_id,
            layout_page_id=str(page.id),
            actor_user_id=None,
        )
        assert bound.is_active is True

        unbound_count = await unbind_category(
            session,
            country="DE",
            module=module_name,
            category_id=category_id,
            actor_user_id=None,
        )
        assert unbound_count >= 1

        active_count_result = await session.execute(
            select(func.count())
            .select_from(LayoutBinding)
            .where(
                and_(
                    LayoutBinding.country == "DE",
                    LayoutBinding.module == module_name,
                    LayoutBinding.category_id == uuid.UUID(category_id),
                    LayoutBinding.is_active.is_(True),
                )
            )
        )
        assert int(active_count_result.scalar() or 0) == 0

        await session.rollback()
