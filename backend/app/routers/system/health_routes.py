from typing import Any, Awaitable, Callable

from fastapi import APIRouter, HTTPException


router = APIRouter()

_health_handler: Callable[[], Awaitable[Any]] | None = None
_health_db_handler: Callable[[], Awaitable[Any]] | None = None
_health_migrations_handler: Callable[[], Awaitable[Any]] | None = None


def register_handlers(
    *,
    health_handler: Callable[[], Awaitable[Any]],
    health_db_handler: Callable[[], Awaitable[Any]],
    health_migrations_handler: Callable[[], Awaitable[Any]],
) -> None:
    global _health_handler, _health_db_handler, _health_migrations_handler
    _health_handler = health_handler
    _health_db_handler = health_db_handler
    _health_migrations_handler = health_migrations_handler


@router.get("/health")
async def health_check_route():
    if not _health_handler:
        raise HTTPException(status_code=503, detail="Health handler not registered")
    return await _health_handler()


@router.get("/health/db")
async def health_db_route():
    if not _health_db_handler:
        raise HTTPException(status_code=503, detail="Health DB handler not registered")
    return await _health_db_handler()


@router.get("/health/migrations")
async def health_migrations_route():
    if not _health_migrations_handler:
        raise HTTPException(status_code=503, detail="Health migrations handler not registered")
    return await _health_migrations_handler()