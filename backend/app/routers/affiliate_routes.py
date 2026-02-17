
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.affiliate import Affiliate
from pydantic import BaseModel, Field
import uuid
import json
import re

router = APIRouter(prefix="/v1/affiliate", tags=["affiliate"])

class AffiliateApplyRequest(BaseModel):
    custom_slug: str = Field(..., min_length=3, max_length=50)
    payout_details: dict

    def validate_slug(self):
        if not re.match("^[a-z0-9-_]+$", self.custom_slug):
            raise ValueError("Slug must be lowercase alphanumeric with hyphens or underscores")

@router.post("/apply", status_code=status.HTTP_201_CREATED)
async def apply_affiliate(
    data: AffiliateApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User applies for affiliate program.
    """
    # 1. Validation
    try:
        data.validate_slug()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Check existing application
    stmt = select(Affiliate).where(Affiliate.user_id == current_user.id)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    
    if existing:
        if existing.status == 'pending':
            raise HTTPException(status_code=400, detail="Application already pending")
        elif existing.status == 'approved':
            raise HTTPException(status_code=400, detail="Already an affiliate")
        elif existing.status == 'rejected':
            # Allow re-apply? For MVP, update existing
            existing.status = 'pending'
            existing.custom_slug = data.custom_slug
            existing.payout_details = data.payout_details
            await db.commit()
            return {"status": "re-applied"}

    # Check slug availability globally
    slug_stmt = select(Affiliate).where(Affiliate.custom_slug == data.custom_slug)
    slug_owner = (await db.execute(slug_stmt)).scalar_one_or_none()
    if slug_owner and slug_owner.user_id != current_user.id:
        raise HTTPException(status_code=409, detail="Slug already taken")

    # 2. Create
    affiliate = Affiliate(
        user_id=current_user.id,
        custom_slug=data.custom_slug,
        payout_details=json.dumps(data.payout_details), # Serialize to JSON string
        status="pending"
    )
    db.add(affiliate)
    await db.commit()
    
    return {"status": "applied", "slug": data.custom_slug}

@router.get("/me")
async def get_my_affiliate_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    stmt = select(Affiliate).where(Affiliate.user_id == current_user.id)
    affiliate = (await db.execute(stmt)).scalar_one_or_none()
    
    if not affiliate:
        return {"status": "none"}
        
    return {
        "status": affiliate.status,
        "slug": affiliate.custom_slug,
        "commission_rate": float(affiliate.commission_rate),
        "link": f"/ref/{affiliate.custom_slug}"
    }
