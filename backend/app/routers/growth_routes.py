
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, check_permissions
from app.models.user import User
from app.services.growth_service import GrowthService
from typing import Optional

router = APIRouter(prefix="/v1/admin/growth", tags=["admin-growth"])

@router.get("/overview")
async def get_growth_overview(
    country: Optional[str] = Query(None, description="Filter by country code (TR, DE, FR)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "finance"]))
):
    service = GrowthService(db)
    return await service.get_overview_stats(country_code=country)
