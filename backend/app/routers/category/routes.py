from typing import Any

from fastapi import APIRouter
from fastapi.routing import APIRoute


router = APIRouter()

_CATEGORY_EXACT_PATHS = {
    "/api/catalog/schema",
    "/api/account/recent-category",
}

_CATEGORY_PREFIXES = (
    "/api/categories",
    "/api/v2/categories/",
    "/api/admin/categories",
)


def _is_category_path(path: str) -> bool:
    if path in _CATEGORY_EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _CATEGORY_PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    kept_routes = []
    moved_routes: list[dict[str, Any]] = []

    for route in source_router.routes:
        if not isinstance(route, APIRoute):
            kept_routes.append(route)
            continue

        if not _is_category_path(route.path):
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
