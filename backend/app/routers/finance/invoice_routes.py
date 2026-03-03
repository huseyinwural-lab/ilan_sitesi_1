from typing import Any

from fastapi import APIRouter

from app.routers.finance.common import delegate_routes_by_matcher


router = APIRouter()

_EXACT_PATHS = {
    "/api/admin/invoices",
    "/api/admin/invoices/export/csv",
    "/api/account/invoices",
    "/api/dealer/invoices",
}

_PREFIXES = (
    "/api/admin/invoices/",
    "/api/account/invoices/",
    "/api/dealer/invoices/",
)


def _is_invoice_path(path: str) -> bool:
    if path in _EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    return delegate_routes_by_matcher(source_router, router, _is_invoice_path)
