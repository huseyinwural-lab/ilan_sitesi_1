from typing import Any

from fastapi import APIRouter

from app.routers.finance.common import delegate_routes_by_matcher


router = APIRouter()

_EXACT_PATHS = {
    "/api/admin/finance/export",
    "/api/admin/finance/overview",
    "/api/admin/finance/revenue",
}

_PREFIXES = (
    "/api/admin/finance/tax-profiles",
    "/api/admin/finance/products",
    "/api/admin/finance/product-prices",
    "/api/admin/finance/trace/",
)


def _is_admin_finance_path(path: str) -> bool:
    if path in _EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    return delegate_routes_by_matcher(source_router, router, _is_admin_finance_path)
