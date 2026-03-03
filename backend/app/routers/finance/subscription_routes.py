from typing import Any

from fastapi import APIRouter

from app.routers.finance.common import delegate_routes_by_matcher


router = APIRouter()

_EXACT_PATHS = {
    "/api/account/subscription",
    "/api/account/subscription/plans",
    "/api/admin/finance/subscriptions",
}

_PREFIXES = (
    "/api/account/subscription/",
    "/api/admin/finance/subscriptions/",
    "/api/admin/subscriptions/",
)


def _is_subscription_path(path: str) -> bool:
    if path in _EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    return delegate_routes_by_matcher(source_router, router, _is_subscription_path)
