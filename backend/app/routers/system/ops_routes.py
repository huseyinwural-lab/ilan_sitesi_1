from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request

from app.dependencies import check_permissions


router = APIRouter()

_ops_health_summary_handler: Callable[[], Awaitable[Any]] | None = None
_ops_health_detail_handler: Callable[[Request], Awaitable[Any]] | None = None

OPS_ALLOWED_ROLES = [
    "super_admin",
    "admin",
    "country_admin",
    "finance",
    "support",
    "moderator",
    "campaigns_admin",
    "campaigns_supervisor",
    "ROLE_AUDIT_VIEWER",
    "ads_manager",
    "pricing_manager",
    "masterdata_manager",
]


def register_handlers(
    *,
    health_summary_handler: Callable[[], Awaitable[Any]],
    health_detail_handler: Callable[[Request], Awaitable[Any]],
) -> None:
    global _ops_health_summary_handler, _ops_health_detail_handler
    _ops_health_summary_handler = health_summary_handler
    _ops_health_detail_handler = health_detail_handler


@router.get("/admin/system/health-summary")
async def ops_health_summary_route(
    current_user=Depends(check_permissions(OPS_ALLOWED_ROLES)),
):
    if not _ops_health_summary_handler:
        raise HTTPException(status_code=503, detail="Ops summary handler not registered")
    return await _ops_health_summary_handler()


@router.get("/admin/system/health-detail")
async def ops_health_detail_route(
    request: Request,
    current_user=Depends(check_permissions(OPS_ALLOWED_ROLES)),
):
    if not _ops_health_detail_handler:
        raise HTTPException(status_code=503, detail="Ops detail handler not registered")
    return await _ops_health_detail_handler(request)