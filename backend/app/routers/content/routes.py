from typing import Any

from fastapi import APIRouter
from fastapi.routing import APIRoute


router = APIRouter()

_CONTENT_EXACT_PATHS = {
    "/api/menu/top-items",
    "/api/site/header",
    "/api/admin/site/header",
    "/api/site/theme",
    "/api/admin/site/theme",
    "/api/site/showcase-layout",
    "/api/site/home-category-layout",
    "/api/site/listing-design",
    "/api/admin/site/home-category-layout",
    "/api/admin/site/listing-design",
    "/api/site/footer",
    "/api/admin/footer/layout",
    "/api/admin/footer/layouts",
    "/api/admin/info-pages",
}

_CONTENT_PREFIXES = (
    "/api/menu/top-items/",
    "/api/admin/menu-items",
    "/api/admin/site/header/",
    "/api/site/assets/",
    "/api/admin/site/theme/",
    "/api/admin/site/showcase-layout",
    "/api/admin/footer/layout/",
    "/api/admin/info-pages/",
    "/api/info/",
)


def _is_content_path(path: str) -> bool:
    if path in _CONTENT_EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _CONTENT_PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    kept_routes = []
    moved_routes: list[dict[str, Any]] = []

    for route in source_router.routes:
        if not isinstance(route, APIRoute):
            kept_routes.append(route)
            continue

        if not _is_content_path(route.path):
            kept_routes.append(route)
            continue

        router.routes.append(route)
        moved_routes.append(
            {
                "path": route.path,
                "name": route.name,
                "methods": sorted(
                    m for m in (route.methods or set()) if m in {"GET", "POST", "PUT", "PATCH", "DELETE"}
                ),
            }
        )

    source_router.routes = kept_routes
    return moved_routes
