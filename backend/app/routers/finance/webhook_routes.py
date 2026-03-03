from typing import Any

from fastapi import APIRouter

from app.routers.finance.common import delegate_routes_by_matcher


router = APIRouter()

_EXACT_PATHS = {
    "/api/payments/webhook",
    "/api/payments/stripe/webhook",
    "/api/webhook/stripe",
    "/api/webhooks/stripe",
}

_PREFIXES = (
    "/api/admin/webhooks/events/",
)


def _is_webhook_path(path: str) -> bool:
    if path in _EXACT_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in _PREFIXES)


def delegate_routes(source_router: APIRouter) -> list[dict[str, Any]]:
    return delegate_routes_by_matcher(source_router, router, _is_webhook_path)
