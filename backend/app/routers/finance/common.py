from typing import Any

from fastapi import APIRouter
from fastapi.routing import APIRoute


def delegate_routes_by_matcher(
    source_router: APIRouter,
    target_router: APIRouter,
    matcher,
) -> list[dict[str, Any]]:
    kept_routes = []
    moved_routes: list[dict[str, Any]] = []

    for route in source_router.routes:
        if not isinstance(route, APIRoute):
            kept_routes.append(route)
            continue

        if not matcher(route.path):
            kept_routes.append(route)
            continue

        target_router.routes.append(route)
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
