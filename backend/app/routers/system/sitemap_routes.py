from typing import Any, Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


router = APIRouter()

_sitemap_index_handler: Callable[[Request], Awaitable[Any]] | None = None
_sitemap_section_handler: Callable[[str, Request, AsyncSession], Awaitable[Any]] | None = None


def register_handlers(
    *,
    sitemap_index_handler: Callable[[Request], Awaitable[Any]],
    sitemap_section_handler: Callable[[str, Request, AsyncSession], Awaitable[Any]],
) -> None:
    global _sitemap_index_handler, _sitemap_section_handler
    _sitemap_index_handler = sitemap_index_handler
    _sitemap_section_handler = sitemap_section_handler


@router.get("/sitemap.xml", include_in_schema=False)
async def sitemap_index_route(request: Request):
    if not _sitemap_index_handler:
        raise HTTPException(status_code=503, detail="Sitemap index handler not registered")
    return await _sitemap_index_handler(request)


@router.get("/sitemaps/{section}.xml", include_in_schema=False)
async def sitemap_section_route(
    section: str,
    request: Request,
    session: AsyncSession = Depends(get_db),
):
    if not _sitemap_section_handler:
        raise HTTPException(status_code=503, detail="Sitemap section handler not registered")
    return await _sitemap_section_handler(section, request, session)